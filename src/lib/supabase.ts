import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let client: SupabaseClient | null = null;

function getSupabaseConfig() {
  const url = import.meta.env.VITE_SUPABASE_URL?.trim();
  const key = import.meta.env.VITE_SUPABASE_ANON_KEY?.trim();
  const table = import.meta.env.VITE_SUPABASE_TABLE?.trim();

  if (!url || !key || !table) {
    return null;
  }

  return { url, key, table };
}

function getClient() {
  const config = getSupabaseConfig();
  if (!config) {
    return null;
  }

  if (!client) {
    client = createClient(config.url, config.key);
  }

  return { client, table: config.table };
}

export async function persistSubmission(
  payload: Record<string, unknown>,
): Promise<"remote" | "local"> {
  const supabase = getClient();

  if (!supabase) {
    const current = JSON.parse(
      window.localStorage.getItem("hausmate-match-submissions") ?? "[]",
    ) as Record<string, unknown>[];

    current.push(payload);
    window.localStorage.setItem(
      "hausmate-match-submissions",
      JSON.stringify(current),
    );
    return "local";
  }

  const { error } = await supabase.client
    .from(supabase.table)
    .insert(payload)
    .select("*")
    .limit(1);

  if (error) {
    throw error;
  }

  return "remote";
}
