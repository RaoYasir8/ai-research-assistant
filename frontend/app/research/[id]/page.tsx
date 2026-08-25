import ResearchRunClient from "@/components/ResearchRunClient";
export default async function ResearchRunPage({ params }: { params: Promise<{ id: string }> }) { const { id } = await params; return <ResearchRunClient id={id} />; }
