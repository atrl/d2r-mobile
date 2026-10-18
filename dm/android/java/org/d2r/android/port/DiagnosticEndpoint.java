package org.d2r.android.port;
import java.net.*;
import java.io.IOException;
final class DiagnosticEndpoint {
    static URL parse(String value) throws Exception {
        URI uri=new URI(value.trim());String host=uri.getHost();
        if(!"https".equals(uri.getScheme())||host==null||!host.endsWith(".trycloudflare.com")
            ||uri.getPort()!=-1||uri.getUserInfo()!=null||uri.getQuery()!=null||uri.getFragment()!=null
            ||!uri.getPath().matches("/v1/[A-Za-z0-9_-]{32}/reports")) throw new IOException("Invalid diagnostic HTTPS address");
        return uri.toURL();
    }
}
