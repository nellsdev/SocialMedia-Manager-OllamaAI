import { InstagramConnect } from "@/components/settings/InstagramConnect";
import { WhatsAppConfig } from "@/components/settings/WhatsAppConfig";

export default function IntegrationsSettingsPage() {
  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Integrations</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Connect your social media accounts to manage content and publishing.
        </p>
      </div>

      <div className="space-y-4">
        <InstagramConnect />
        <WhatsAppConfig />
      </div>
    </div>
  );
}
