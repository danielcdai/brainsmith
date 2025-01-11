import { BACKEND_URL } from "$lib/constants.js";

export const login = async () => {
    const url = BACKEND_URL + '/auth/login';
    return await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
}

export const callback = async (data:any) => {
    const url = BACKEND_URL + '/auth/callback';
    return await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
}