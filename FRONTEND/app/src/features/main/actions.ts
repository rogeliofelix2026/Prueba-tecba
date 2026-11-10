"use server";

import OpenAI from "openai";

const groq = new OpenAI({
  apiKey: process.env.GROQ_TOKEN,
  baseURL: "https://api.groq.com/openai/v1",
});

// Caches en memoria
const parseCache = new Map<string, { actividad: string; direccion: string }>();
const territoryCache = new Map<string, any>();

export type ParseResult = {
  actividad: string;
  direccion: string;
  error?: string;
};

export async function parseWithGroq(texto: string): Promise<ParseResult> {
  if (!texto?.trim()) {
    return { actividad: "", direccion: "", error: "El texto está vacío" };
  }

  const key = texto.trim().toLowerCase();

  // Cache hit
  if (parseCache.has(key)) {
    return parseCache.get(key)!;
  }

  try {
    const completion = await groq.chat.completions.create({
      model: "qwen/qwen3.8-27b",
      temperature: 0.1,
      max_tokens: 120,
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content: `Extraé actividad y dirección. Devolvé solo este JSON:
{"actividad":"tipo de negocio","direccion":"calle y número limpio"}

Reglas para la dirección:
- Sacá palabras como "al", "en", "número", etc.
- Formato: "Corrientes 5000" o "Av. Corrientes 5000"
- Sin "al" ni texto extra.`,
        },
        {
          role: "user",
          content: texto.trim(),
        },
      ],
    });

    const content = completion.choices[0]?.message?.content;
    if (!content) {
      return { actividad: "", direccion: "", error: "Sin respuesta de Groq" };
    }

    const parsed = JSON.parse(content);
    const result = {
      actividad: parsed.actividad?.trim() || "",
      direccion: parsed.direccion?.trim() || "",
    };

    parseCache.set(key, result);
    return result;
  } catch (err: any) {
    console.error("Error Groq:", err);
    return {
      actividad: "",
      direccion: "",
      error: err?.message || "Error al consultar Groq",
    };
  }
}

export async function consultarTerritorioConDatos(
  actividad: string,
  direccion: string
) {
  const key = `${actividad.toLowerCase()}|${direccion.toLowerCase()}`;

  // Cache hit
  if (territoryCache.has(key)) {
    return territoryCache.get(key);
  }

  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) throw new Error("BACKEND_URL no configurada");

  const res = await fetch(`${backendUrl}/api/v1/territory`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      activity: actividad,
      address: direccion,
    }),
    cache: "no-store",
  });

  if (!res.ok) {
    let message = "Error al consultar el backend";

    switch (res.status) {
      case 404:
        message = "No se pudo identificar la dirección ingresada.";
        break;
      case 422:
        message = "La dirección tiene un formato inválido o no se puede interpretar.";
        break;
      case 502:
        message = "El servicio de geocodificación no está disponible en este momento.";
        break;
      case 503:
        message = "El sistema no está disponible. Intentá de nuevo más tarde.";
        break;
      default:
        try {
          const err = await res.json();
          message = err?.detail || err?.message || message;
        } catch {
          // ignore
        }
    }

    throw new Error(message);
  }

  const data = await res.json();
  territoryCache.set(key, data);
  return data;
}

export async function preguntarSobrePaso(
  pregunta: string,
  pasoTitulo: string,
  pasoDescripcion: string
): Promise<{ respuesta: string; error?: string }> {
  if (!pregunta?.trim()) {
    return { respuesta: "", error: "Escribí una consulta antes de enviar." };
  }

  try {
    const completion = await groq.chat.completions.create({
      model: "qwen/qwen3.8-27b",
      temperature: 0.2,
      max_tokens: 280,
      messages: [
        {
          role: "system",
          content: `Sos un asistente orientativo del Gobierno de la Ciudad de Buenos Aires (GCBA) para el trámite "Habilitación de Actividad Económica" ante la Agencia Gubernamental de Control (AGC / DGHP).
Respondé de forma breve, clara y basada únicamente en la información oficial:
- Plataforma: SSIT con usuario y clave miBA nivel 3.
- Vía exprés: locales de hasta 200 m² que cumplan condiciones de ubicación, accesibilidad, sin entrepisos, sin áreas especiales ni edificios catalogados, y sin inflamables/explosivos.
- Documentación base: 1) Formulario de conformación de la unidad de uso (DDJJ de la actividad), 2) Anexo Técnico firmado por profesional responsable (incluye encomienda profesional, datos del profesional, información de unidad de uso, mixtura/área especial, croquis de ubicación y DDJJ de verificación del local).
- Documentación adicional condicional: Certificado de sobrecarga, Plano de Uso de Actividad Económica, Autorización de Emplazamiento y documentación específica del rubro.
- Al declarar la ubicación y guardar la solicitud se generan el Número de Trámite y el Código de Seguridad (indispensables para el Anexo Técnico).
- Certificado de Aptitud Ambiental (CAA): se tramita en Impacto Ambiental.
- Evaluación DGHP: puede aprobar, observar, rechazar o librar al uso (entrega oblea con QR y acceso al Libro de Registro de Inspecciones Digital; librado al uso permite operar pero no equivale a la habilitación definitiva).
Paso activo actual: "${pasoTitulo}" (${pasoDescripcion}).
No uses formato markdown complejo ni inventes requisitos fuera de esta base.`,
        },
        {
          role: "user",
          content: pregunta.trim(),
        },
      ],
    });

    const content = completion.choices[0]?.message?.content?.trim();
    if (!content) {
      return { respuesta: "", error: "No se pudo obtener respuesta en este momento." };
    }
    return { respuesta: content };
  } catch (err: any) {
    console.error("Error Groq pregunta:", err);
    return {
      respuesta: "",
      error: "No se pudo procesar tu consulta en este momento.",
    };
  }
}

function parseUsigJsonp(text: string): any {
  let value = text.trim().replace(/;$/, "").trim();
  if (value.startsWith("(") && value.endsWith(")")) {
    value = value.slice(1, -1).trim();
  }
  const jsonpMatch = value.match(/^[a-zA-Z0-9_$.]+\s*\(([\s\S]*)\)$/);
  if (jsonpMatch) {
    value = jsonpMatch[1].trim();
  }
  return JSON.parse(value);
}

async function fetchUsigPuerta(lat: number, lng: number): Promise<string | null> {
  try {
    const res = await fetch(
      `https://ws.usig.buenosaires.gob.ar/geocoder/2.2/reversegeocoding?x=${lng}&y=${lat}`,
      { cache: "no-store" }
    );
    if (!res.ok) return null;
    const text = await res.text();
    const data = parseUsigJsonp(text);
    const puerta = data?.puerta;
    if (typeof puerta === "string" && puerta.trim() && /\d+/.test(puerta)) {
      return puerta.replace(/,\s*CABA$/i, "").trim();
    }
  } catch {
    // ignorar y probar siguiente método
  }
  return null;
}

export async function reverseGeocodeCoordenadas(
  lat: number,
  lng: number
): Promise<string> {
  // 1. Geocoder reverso oficial de parcelas/puertas de USIG (devuelve calle y altura exacta en "puerta")
  const puertaExacta = await fetchUsigPuerta(lat, lng);
  if (puertaExacta) {
    return puertaExacta;
  }

  // 2. Si el clic cayó sobre la calzada o esquina sin puerta directa, probar desplazamientos cortos (~15m) hacia las parcelas vecinas
  const offsets = [
    [0.00014, 0],
    [-0.00014, 0],
    [0, 0.00014],
    [0, -0.00014],
    [0.00014, 0.00014],
    [-0.00014, -0.00014],
  ];
  for (const [dLat, dLng] of offsets) {
    const puertaVecina = await fetchUsigPuerta(lat + dLat, lng + dLng);
    if (puertaVecina) {
      return puertaVecina;
    }
  }

  // 3. Normalizador USIG por coordenadas (solo si incluye altura numérica, descartando cruces "Calle A y Calle B")
  try {
    const usigRes = await fetch(
      `https://servicios.usig.buenosaires.gob.ar/normalizar/?lng=${lng}&lat=${lat}`,
      { cache: "no-store" }
    );
    if (usigRes.ok) {
      const usigData = await usigRes.json();
      const candidatos: string[] = [
        usigData?.direccion,
        ...(Array.isArray(usigData?.direccionesNormalizadas)
          ? usigData.direccionesNormalizadas.map((d: any) => d?.direccion)
          : []),
      ].filter((d): d is string => typeof d === "string" && d.trim().length > 0);

      const conAltura = candidatos.find((dir) => /\d+/.test(dir));
      if (conAltura) {
        return conAltura.replace(/,\s*CABA$/i, "").trim();
      }
    }
  } catch {
    // Continuar con Nominatim
  }

  // 4. Fallback con Nominatim (OpenStreetMap) con zoom de nivel edificio (18)
  try {
    const nomRes = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1&accept-language=es`,
      {
        headers: {
          "User-Agent": "SistemaGestionInteligente-CABA/1.0",
        },
        cache: "no-store",
      }
    );
    if (nomRes.ok) {
      const nomData = await nomRes.json();
      const road = nomData?.address?.road;
      const rawHouseNumber = String(nomData?.address?.house_number ?? "");
      const houseNumber = rawHouseNumber.match(/\d+/)?.[0];
      if (road && houseNumber) {
        return `${road} ${houseNumber}`;
      }
      if (road) {
        return road;
      }
    }
  } catch {
    // Fallback final
  }

  return `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
}

export async function extraerActividadDesdeTexto(texto: string): Promise<string> {
  const limpio = texto.trim();
  if (!limpio) return "";

  const limpiarPrefijos = (str: string) =>
    str
      .replace(
        /^(quiero|quisiera|me gustaría|necesito|voy a|pensaba)?\s*(abrir|poner|habilitar|iniciar|instalar|montar)?\s*(un|una|el|la|los|las|mi)?\s+/i,
        ""
      )
      .trim();

  try {
    const completion = await groq.chat.completions.create({
      model: "qwen/qwen3.8-27b",
      temperature: 0.1,
      max_tokens: 60,
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content: `Extraé únicamente el rubro o tipo de negocio/actividad del texto del usuario. Devolvé solo este JSON:
{"actividad":"tipo de negocio"}
Ejemplo: "abrir una cafetería" -> {"actividad":"cafetería"}`,
        },
        {
          role: "user",
          content: limpio,
        },
      ],
    });

    const content = completion.choices[0]?.message?.content;
    if (content) {
      const parsed = JSON.parse(content);
      if (parsed?.actividad?.trim()) {
        return parsed.actividad.trim();
      }
    }
  } catch {
    // Fallback determinístico si Groq no responde
  }

  return limpiarPrefijos(limpio) || limpio;
}

