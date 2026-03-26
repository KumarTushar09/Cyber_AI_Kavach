import { NextRequest, NextResponse } from "next/server";

const BACKEND_BASE = process.env.BACKEND_INTERNAL_API_BASE || "http://127.0.0.1:8000/api/v1";

export async function POST(request: NextRequest, context: { params: { path: string[] } }) {
  const path = (context.params.path || []).join("/");
  const target = new URL(`${BACKEND_BASE.replace(/\/$/, "")}/${path}`);
  target.search = request.nextUrl.search;

  const contentType = request.headers.get("content-type") || "application/json";
  const body = await request.arrayBuffer();

  try {
    const headers: Record<string, string> = {};
    if (contentType) {
      headers["Content-Type"] = contentType;
    }

    const upstream = await fetch(target.toString(), {
      method: "POST",
      headers,
      body,
    });

    const responseBody = await upstream.arrayBuffer();
    return new NextResponse(responseBody, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") || "application/json",
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: "error",
        data: {},
        errors: [{ code: "PROXY_ERROR", message: `Failed to reach backend: ${String(error)}` }],
      },
      { status: 502 }
    );
  }
}
