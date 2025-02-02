import type { SvelteComponent } from "svelte";
import GitHub from "./github.svelte";
import Google from "./google.svelte";

export type Icon = SvelteComponent;

export const Icons = {
	gitHub: GitHub,
    google: Google,
};