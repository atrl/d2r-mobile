package org.d2r.android.port;
public class DiagnosticEndpointTest {
 public static void main(String[] args)throws Exception{
  String path="/v1/01234567890123456789012345678901/reports";
  DiagnosticEndpoint.parse("https://test.trycloudflare.com"+path);
  for(String url:new String[]{"http://test.trycloudflare.com"+path,"https://test.trycloudflare.com.evil.test"+path,"https://127.0.0.1"+path,"https://user@test.trycloudflare.com"+path,"https://test.trycloudflare.com"+path+"?token=x","https://test.trycloudflare.com/v1/wrong/reports"}){
   try{DiagnosticEndpoint.parse(url);throw new AssertionError("Accepted "+url);}catch(java.io.IOException expected){}
  }
  System.out.println("Diagnostic endpoint rejects insecure, wrong-host and malformed credential URLs");
 }
}
