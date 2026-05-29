import { Link } from "react-router-dom";
import { googleAuthUrl } from "../api";
import SpongeComputerIllustration from "./SpongeComputerIllustration";

type Props = {
  googleConnected: boolean;
  hasSynced: boolean;
  onCheckAgain: () => void;
  checking?: boolean;
};

export default function OnboardingSplash({
  googleConnected,
  hasSynced,
  onCheckAgain,
  checking = false,
}: Props) {
  const step1Done = googleConnected;
  const step2Done = hasSynced;

  return (
    <div className="max-w-lg mx-auto text-center space-y-6 py-4">
      <SpongeComputerIllustration className="w-full max-w-md mx-auto rounded-xl shadow-md border border-gray-200" />

      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-rh-dark">Oopsie!</h1>
        <p className="text-lg text-gray-700">
          You need to connect to Google so I can do things for you.
        </p>
      </div>

      <ol className="text-left text-sm space-y-3 bg-white border rounded-lg p-4 shadow-sm">
        <li className="flex gap-3 items-start">
          <span
            className={`shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
              step1Done ? "bg-green-600 text-white" : "bg-gray-200 text-gray-600"
            }`}
          >
            {step1Done ? "✓" : "1"}
          </span>
          <div>
            <p className="font-medium">Connect Google</p>
            <p className="text-gray-600 text-xs mt-0.5">
              Gmail, Calendar, and Drive (read-only) so tasks and contacts can sync.
            </p>
            {!step1Done && (
              <a
                href={googleAuthUrl()}
                className="inline-block mt-2 bg-rh-red text-white px-4 py-2 rounded text-sm hover:opacity-90"
              >
                Connect Google
              </a>
            )}
          </div>
        </li>
        <li className="flex gap-3 items-start">
          <span
            className={`shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
              step2Done ? "bg-green-600 text-white" : "bg-gray-200 text-gray-600"
            }`}
          >
            {step2Done ? "✓" : "2"}
          </span>
          <div>
            <p className="font-medium">Run your first sync</p>
            <p className="text-gray-600 text-xs mt-0.5">
              In Settings, click <strong>Run sync now</strong> and wait until it finishes.
            </p>
            {step1Done && !step2Done && (
              <Link
                to="/settings"
                className="inline-block mt-2 bg-rh-dark text-white px-4 py-2 rounded text-sm hover:opacity-90"
              >
                Open Settings → Sync
              </Link>
            )}
          </div>
        </li>
      </ol>

      <div className="flex flex-wrap justify-center gap-3">
        <Link to="/settings" className="text-sm text-rh-red hover:underline">
          Settings
        </Link>
        <button
          type="button"
          onClick={onCheckAgain}
          disabled={checking}
          className="text-sm bg-white border border-gray-300 px-4 py-2 rounded hover:bg-gray-50 disabled:opacity-50"
        >
          {checking ? "Checking…" : "I've done this — refresh"}
        </button>
      </div>
    </div>
  );
}
