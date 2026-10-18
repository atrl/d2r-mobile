package org.d2r.android.port;
public class ScreenResolutionTest {
 public static void main(String[] args){
  for(int[] window:new int[][]{{2748,1172},{2480,2200},{1280,720},{800,600},{1172,2748}}){
   int[] render=ScreenResolution.match(window[0],window[1]);double ratio=(double)render[0]/render[1],expected=Math.max(16.0/9,(double)window[0]/window[1]);
   if(Math.abs(ratio/expected-1)>.006||render[0]>2560||render[1]>900)throw new AssertionError("Aspect or render budget changed");
  }
  if(ScreenResolution.match(0,0)[0]!=1600)throw new AssertionError();
  System.out.println("Narrow screens safely use 16:9; ultrawide rendering preserves aspect under budget");
 }
}
