interface ImportMetaEnv {
	readonly PUBLIC_SUPABASE_URL?: string;
	readonly PUBLIC_SUPABASE_PUBLISHABLE_KEY?: string;
	readonly PUBLIC_API_BASE_URL?: string;
}

interface ImportMeta {
	readonly env: ImportMetaEnv;
}
