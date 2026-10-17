import { AuthForm } from "@/components/auth-form";

export function AuthPage({ mode }: { mode: "login" | "register" }) {
	return <AuthForm mode={mode} />;
}
