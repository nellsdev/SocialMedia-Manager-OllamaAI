import { IdeaBankList } from "@/components/ideas/IdeaBankList";

export default function IdeasPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Idea Bank</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Capture, browse, and convert content ideas into posts.
        </p>
      </div>
      <IdeaBankList />
    </div>
  );
}
