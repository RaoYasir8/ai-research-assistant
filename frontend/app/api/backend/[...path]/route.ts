import { NextRequest } from "next/server";

const backend = process.env.BACKEND_INTERNAL_URL || "http://backend:8000";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = new URL(`${backend.replace(/\/$/, "")}/${path.join("/")}`);
  request.nextUrl.searchParams.forEach((value, key) => target.searchParams.append(key, value));

  const headers = new Headers();
  for (const [key, value] of request.headers.entries()) {
    if (!["host", "content-length", "connection"].includes(key.toLowerCase())) headers.set(key, value);
  }

  const hasBody = !["GET", "HEAD"].includes(request.method);
  const upstream = await fetch(target, {
    method: request.method,
    headers,
    body: hasBody ? await request.arrayBuffer() : undefined,
    redirect: "manual",
    cache: "no-store",
  });

  const responseHeaders = new Headers();
  upstream.headers.forEach((value, key) => {
    if (key.toLowerCase() !== "set-cookie" && key.toLowerCase() !== "content-encoding") {
      responseHeaders.set(key, value);
    }
  });
  const cookieHeaders = (upstream.headers as Headers & { getSetCookie?: () => string[] }).getSetCookie?.() || [];
  if (cookieHeaders.length) {
    cookieHeaders.forEach((cookie) => responseHeaders.append("set-cookie", cookie));
  } else {
    const cookie = upstream.headers.get("set-cookie");
    if (cookie) responseHeaders.append("set-cookie", cookie);
  }

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
