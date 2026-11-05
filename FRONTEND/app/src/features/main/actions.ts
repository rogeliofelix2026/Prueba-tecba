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
