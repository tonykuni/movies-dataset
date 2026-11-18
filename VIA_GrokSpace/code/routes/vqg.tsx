import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/vqg")({
  loader: () => {
    throw redirect({ to: "/", hash: "vqg" });
  },
});
