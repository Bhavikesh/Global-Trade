import { NextRequest, NextResponse } from "next/server";
import { auth0 } from "@/lib/auth0";

const BACKEND_URL =
  process.env.INTERNAL_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8001/api";

async function forwardRequest(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const targetPath = "/" + path.join("/");
  const url = `${BACKEND_URL}${targetPath}${request.nextUrl.search}`;

  let accessToken: string | undefined;
  try {
    const tokenResult = await auth0.getAccessToken();
    accessToken = tokenResult?.token;
  } catch {
    // Unauthenticated or token unavailable
  }

  const headers = new Headers();
  headers.set("Content-Type", "application/json");
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const init: RequestInit = {
    method: request.method,
    headers,
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    try {
      const body = await request.text();
      if (body) {
        init.body = body;
      }
    } catch {
      // no body
    }
  }

  try {
    const backendRes = await fetch(url, init);
    const contentType = backendRes.headers.get("content-type") || "";
    if (backendRes.status === 204) {
      return new NextResponse(null, { status: 204 });
    }
    if (contentType.includes("application/json")) {
      const data = await backendRes.json();
      return NextResponse.json(data, { status: backendRes.status });
    }
    const text = await backendRes.text();
    return new NextResponse(text, { status: backendRes.status });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    return NextResponse.json(
      { detail: `Backend communication error: ${message}` },
      { status: 502 }
    );
  }
}

export const GET = forwardRequest;
export const POST = forwardRequest;
export const PATCH = forwardRequest;
export const DELETE = forwardRequest;
