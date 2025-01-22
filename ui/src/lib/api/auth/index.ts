import { BACKEND_URL } from "$lib/constants.js";

export const login = async () => {
    const url = BACKEND_URL + '/api/v1/auth/login';
    return await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
}

export const callback = async (data:any) => {
    const url = BACKEND_URL + '/api/v1/auth/callback';
    return await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
}

export const getUser = async (access_token:string) => {
    const url = BACKEND_URL + '/api/v1/auth/user?access_token='+access_token;
    return await fetch(url, {
        method: 'GET',
        credentials: 'include'
    });
}