"use server";

export async function queryOverpassAction(query: string, retries = 3): Promise<any> {
  const OVERPASS_TOKEN = process.env.OVERPASS_TOKEN;
  if (!OVERPASS_TOKEN) throw new Error("Falta OVERPASS_TOKEN");

  const OVERPASS_URL = `https://overpass.nextgis.com/my-${OVERPASS_TOKEN}/api/interpreter`;

  for (let i = 0; i < retries; i++) {
    const response = await fetch(OVERPASS_URL, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: `data=${encodeURIComponent(query)}`,
      cache: "no-store",
    });

    const text = await response.text();

    if (text.includes("duplicate_query")) {
      console.log(`[Overpass] Duplicate, reintento ${i + 1}/${retries}`);
      await new Promise(r => setTimeout(r, 1500 * (i + 1)));
      continue;
    }

    if (!response.ok || text.trim().startsWith("<")) {
      throw new Error(`Overpass error (${response.status}): ${text.slice(0, 200)}`);
    }

    return JSON.parse(text);
  }

  throw new Error("Overpass: máximo de reintentos alcanzado");
}