import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { UDXScreen } from "../../../components/UDXScreen";
import { screenBySlug, screens } from "../../../lib/screens";

export const dynamicParams = false;

export function generateStaticParams() {
  return screens.map((screen) => ({ id: screen.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  const screen = screenBySlug.get(id);
  return { title: screen ? `${screen.id} · ${screen.name} | UDX Pay` : "Tela UDX" };
}

export default async function ScreenPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const screen = screenBySlug.get(id);
  if (!screen) notFound();
  const index = screens.findIndex((item) => item.id === screen.id);
  return <UDXScreen screen={screen} previous={screens[index - 1]} next={screens[index + 1]} />;
}
