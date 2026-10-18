package org.d2r.android.port;
/** Fit a render budget while preserving the current window's aspect, never stretching pixels. */
final class ScreenResolution {
    static int[] match(int width,int height) {
        if(width<=0||height<=0||(long)width*9<(long)height*16)return new int[]{1600,900};
        double scale=Math.min(900.0/height,2560.0/width);
        int w=Math.max(320,((int)Math.round(width*scale)+2)/4*4);
        int h=Math.max(240,((int)Math.round(height*scale)+2)/4*4);
        return new int[]{Math.min(2560,w),Math.min(900,h)};
    }
}
