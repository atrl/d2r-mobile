package org.d2r.android.port;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.widget.EditText;
import java.net.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;

/** Explicitly enabled, write-only diagnostics. No endpoint or credential is bundled. */
final class AutoDiagnostics {
    private static ScheduledExecutorService worker;
    private static SharedPreferences prefs(Context c) { return c.getSharedPreferences("auto-diagnostics",0); }
    private static String text(Context c,String key) { return c.getString(c.getResources().getIdentifier(key,"string",c.getPackageName())); }
    static boolean enabled(Context c) { return prefs(c).getBoolean("enabled",false); }
    static synchronized void start(Context context) {
        if (!enabled(context) || worker!=null) return;
        Context app=context.getApplicationContext();
        worker=Executors.newSingleThreadScheduledExecutor(r->{Thread t=new Thread(r,"d2r-auto-diagnostics");t.setDaemon(true);return t;});
        worker.scheduleWithFixedDelay(()->send(app),0,30,TimeUnit.SECONDS);
    }
    private static synchronized void stop(Context context) {
        prefs(context).edit().putBoolean("enabled",false).apply();
        if(worker!=null){worker.shutdownNow();worker=null;}
    }
    private static void send(Context c) {
        HttpURLConnection connection=null;
        try {
            if(!enabled(c))return;
            URL address=DiagnosticEndpoint.parse(prefs(c).getString("endpoint",""));
            byte[] body=StartupDiagnostics.collect(c).getBytes(StandardCharsets.UTF_8);
            if(body.length>262144)throw new IOException("Report exceeds upload limit");
            connection=(HttpURLConnection)address.openConnection();connection.setInstanceFollowRedirects(false);
            connection.setConnectTimeout(10000);connection.setReadTimeout(15000);connection.setRequestMethod("POST");
            connection.setRequestProperty("Content-Type","text/plain; charset=utf-8");connection.setDoOutput(true);connection.setFixedLengthStreamingMode(body.length);
            if(!enabled(c))return;
            try(OutputStream out=connection.getOutputStream()){out.write(body);}
            int code=connection.getResponseCode();if(code!=202)throw new IOException("HTTP "+code);
            prefs(c).edit().putString("last",text(c,"dmAndroidAutoSent")+" "+new java.text.SimpleDateFormat("HH:mm:ss",java.util.Locale.ROOT).format(new java.util.Date())).apply();
        } catch(Exception error) {
            // Never echo the endpoint/token or an exception that might include it.
            prefs(c).edit().putString("last",text(c,"dmAndroidAutoFailed")).apply();
        } finally {if(connection!=null)connection.disconnect();}
    }
    static void configure(Activity activity) {
        if(enabled(activity)) {
            new AlertDialog.Builder(activity).setTitle(text(activity,"dmAndroidAutoTitle"))
                .setMessage(text(activity,"dmAndroidAutoEnabled")+"\n"+prefs(activity).getString("last",""))
                .setPositiveButton(text(activity,"dmAndroidAutoDisable"),(d,w)->stop(activity))
                .setNegativeButton(android.R.string.cancel,null).show();return;
        }
        EditText input=new EditText(activity);input.setSingleLine(true);input.setInputType(android.text.InputType.TYPE_CLASS_TEXT|android.text.InputType.TYPE_TEXT_VARIATION_URI);
        input.setHint("https://…trycloudflare.com/v1/…/reports");input.setText(prefs(activity).getString("endpoint",""));
        AlertDialog dialog=new AlertDialog.Builder(activity).setTitle(text(activity,"dmAndroidAutoTitle"))
            .setMessage(text(activity,"dmAndroidAutoNotice")).setView(input)
            .setPositiveButton(text(activity,"dmAndroidAutoEnable"),null).setNegativeButton(android.R.string.cancel,null).create();
        dialog.setOnShowListener(d->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{
            try {String url=DiagnosticEndpoint.parse(input.getText().toString()).toExternalForm();prefs(activity).edit().putString("endpoint",url).putBoolean("enabled",true).apply();start(activity);dialog.dismiss();}
            catch(Exception error){input.setError(text(activity,"dmAndroidAutoInvalid"));}
        }));dialog.show();
    }
}
