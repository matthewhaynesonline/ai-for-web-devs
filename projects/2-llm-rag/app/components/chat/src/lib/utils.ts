async function doRequest(url: string, body, aborter, method: string = "POST") {
  let response = null;

  try {
    if (method === "GET" || method === "HEAD") {
      response = await fetch(url, {
        signal: aborter.signal,
        method: method,
        headers: { "Content-Type": "application/json" },
      });
    } else {
      response = await fetch(url, {
        signal: aborter.signal,
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    }
  } catch (err) {
    console.warn(err.message);
  }

  return response;
}

function throttle(func, limit: number) {
  let inThrottle: boolean;

  return function () {
    const args = arguments;
    const context = this;

    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

export { doRequest, throttle };
