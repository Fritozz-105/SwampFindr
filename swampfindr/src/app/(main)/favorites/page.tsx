import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import { FavoritesView } from "@/components/features/FavoritesView";

export default async function FavoritesPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/auth/login");

  return <FavoritesView />;
}
