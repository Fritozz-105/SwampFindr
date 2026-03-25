import { Suspense } from "react";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { SearchView } from "@/components/features/SearchView";

export default async function SearchPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth/login");
  }

  return (
    <Suspense>
      <SearchView />
    </Suspense>
  );
}
