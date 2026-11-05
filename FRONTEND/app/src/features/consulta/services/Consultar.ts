import consulta from "../../mapa/fixtures/consulta.json"

export async function consultar(texto: string) {
  // Simulamos un retardo de red de 700ms para poder apreciar el estado de carga
  await new Promise((resolve) => setTimeout(resolve, 700))

  // Si escribes la palabra "error", simula una falla del servidor para probar la alerta de error
  if (texto.toLowerCase().includes("error")) {
    throw new Error("Error simulado: no se pudo obtener respuesta del servidor.")
  }

  return {
    ...consulta,
    query: texto,
    answer: `Información de trámites encontrada para: "${texto}"`,
  }
}