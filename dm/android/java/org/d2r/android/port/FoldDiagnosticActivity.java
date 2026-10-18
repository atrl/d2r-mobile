package org.d2r.android.port;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.MotionEvent;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

/** No game content: exercise real Android surface callbacks, density and touch. */
public final class FoldDiagnosticActivity extends Activity implements SurfaceHolder.Callback {
    private SurfaceView view;
    private int creates, changes, destroys;
    private float touchX = -1, touchY = -1;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        view = new SurfaceView(this);
        view.getHolder().addCallback(this);
        view.setOnTouchListener((v, e) -> {
            touchX = e.getActionMasked() == MotionEvent.ACTION_CANCEL ? -1 : e.getX();
            touchY = e.getY(); draw(); return true;
        });
        setContentView(view);
    }
    public void surfaceCreated(SurfaceHolder h) { creates++; }
    public void surfaceDestroyed(SurfaceHolder h) { destroys++; touchX = -1; }
    public void surfaceChanged(SurfaceHolder h, int format, int width, int height) {
        changes++; touchX = -1; draw();
    }
    @Override public void onConfigurationChanged(android.content.res.Configuration config) {
        super.onConfigurationChanged(config); touchX = -1; view.post(this::draw);
    }
    private void draw() {
        if (!view.getHolder().getSurface().isValid()) return;
        Canvas c = view.getHolder().lockCanvas();
        if (c == null) return;
        try {
            c.drawColor(Color.BLACK);
            float w=c.getWidth(), h=c.getHeight(), gw=w, gh=w*9/16;
            if (gh>h) { gh=h; gw=h*16/9; }
            float left=(w-gw)/2, top=(h-gh)/2;
            paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(3); paint.setColor(Color.GREEN);
            c.drawRect(left+2,top+2,left+gw-2,top+gh-2,paint);
            c.drawLine(left,top,left+gw,top+gh,paint);
            c.drawLine(left+gw,top,left,top+gh,paint);
            paint.setStyle(Paint.Style.FILL); paint.setTextSize(Math.min(30*getResources().getDisplayMetrics().density,w/30));
            paint.setColor(Color.WHITE);
            float line=paint.getTextSize()*1.4f;
            c.drawText("Window " + (int)w + " x " + (int)h,16,line,paint);
            c.drawText("Surface create/change/destroy: "+creates+"/"+changes+"/"+destroys,16,line*2,paint);
            c.drawText("Fold, rotate, tap. Back to exit.",16,line*3,paint);
            c.drawText("Android Canvas check; not a Vulkan/game test.",16,line*4,paint);
            if(touchX>=0) { paint.setColor(Color.YELLOW); c.drawCircle(touchX,touchY,12,paint); }
        } finally { view.getHolder().unlockCanvasAndPost(c); }
    }
}
