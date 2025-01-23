import { base } from '$app/paths';

/** @type {import('@sveltejs/kit').HandleClient} */
export async function handle({ event, resolve }) {
    const url = new URL(event.url);
    console.log('url: ',url.pathname);
    if (!url.pathname.startsWith(base)) {
        url.pathname = `${base}${url.pathname}`;
        return event.navigation.goto(url.pathname, { replaceState: true });
    }

    return resolve(event);
}