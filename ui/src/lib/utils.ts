import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { goto as svelteGoto } from '$app/navigation';
import { base } from '$app/paths';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}



export function goto(path, options = {}) {
    const fullPath = path.startsWith(base) ? path : `${base}${path}`;
    svelteGoto(fullPath, options);
}
