import { writable } from 'svelte/store';

/**
 * Our auth store holds the JWT (if the user is logged in).
 * If null, user is considered logged out.
 */
export const authToken = writable<string | null>(null);