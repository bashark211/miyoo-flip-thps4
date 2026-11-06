/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 bashark211
 */
#define _POSIX_C_SOURCE 200809L
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <signal.h>
static volatile sig_atomic_t alive=1;
static int xerror(Display*d,XErrorEvent*e){(void)d;(void)e;return 0;}
static void stop(int n){(void)n;alive=0;}
static void nap(void){struct timespec t={1,0};nanosleep(&t,NULL);}
static Window find_game(Display*d,Window root,int depth){
 if(depth>6)return 0;
 char *name=NULL;
 int match=0;XClassHint hint={0};
 if(XGetClassHint(d,root,&hint)){match=(hint.res_name&&!strcmp(hint.res_name,"skate4.exe"))||(hint.res_class&&!strcmp(hint.res_class,"skate4.exe"));if(hint.res_name)XFree(hint.res_name);if(hint.res_class)XFree(hint.res_class);}
 if(!match&&XFetchName(d,root,&name)&&name){match=!strcmp(name,"THPS4");XFree(name);}
 if(match){XWindowAttributes a;if(XGetWindowAttributes(d,root,&a)&&a.map_state==IsViewable&&a.width>=600&&a.height>=400)return root;}
 Window rt,pa,*children=NULL;unsigned int n=0;Window out=0;
 if(XQueryTree(d,root,&rt,&pa,&children,&n)){for(unsigned int i=0;i<n&&!out;i++)out=find_game(d,children[i],depth+1);if(children)XFree(children);}return out;
}
int main(int argc,char**argv){
 Display*d=XOpenDisplay(NULL);if(!d){fprintf(stderr,"Display connection not ready\n");return 2;}XSetErrorHandler(xerror);XSync(d,False);
 if(argc==2&&!strcmp(argv[1],"--ready")){printf("X11_READY %s %dx%d\n",DisplayString(d),DisplayWidth(d,DefaultScreen(d)),DisplayHeight(d,DefaultScreen(d)));XCloseDisplay(d);return 0;}
 if(argc!=2||strcmp(argv[1],"--temperature")){fprintf(stderr,"usage: display-helper --ready|--temperature\n");XCloseDisplay(d);return 2;}
 signal(SIGTERM,stop);signal(SIGINT,stop);Window parent=0,hud=0;GC gc=0;int screen=DefaultScreen(d);XFontStruct*font=XLoadQueryFont(d,"fixed");
 while(alive){
  XWindowAttributes a;if(parent&&(!XGetWindowAttributes(d,parent,&a)||a.map_state!=IsViewable)){if(gc)XFreeGC(d,gc);gc=0;parent=0;hud=0;}
  if(!parent){parent=find_game(d,DefaultRootWindow(d),0);if(!parent){nap();continue;}
   hud=XCreateSimpleWindow(d,parent,8,28,132,18,0,WhitePixel(d,screen),BlackPixel(d,screen));XSetWindowAttributes at={.override_redirect=True};XChangeWindowAttributes(d,hud,CWOverrideRedirect,&at);XStoreName(d,hud,"THPS4 temperature");gc=XCreateGC(d,hud,0,NULL);XSetForeground(d,gc,WhitePixel(d,screen));XSetBackground(d,gc,BlackPixel(d,screen));if(font)XSetFont(d,gc,font->fid);XMapRaised(d,hud);fprintf(stderr,"Temperature overlay attached parent=0x%lx child=0x%lx\n",parent,hud);
  }
  FILE*f=fopen("/sys/class/thermal/thermal_zone0/temp","r");long t=0;int valid=f&&fscanf(f,"%ld",&t)==1;if(f)fclose(f);char text[40];if(valid)snprintf(text,sizeof(text),"CPU: %.1f C",t/1000.0);else snprintf(text,sizeof(text),"CPU: unavailable");
  XClearWindow(d,hud);XDrawImageString(d,hud,gc,3,13,text,(int)strlen(text));XRaiseWindow(d,hud);XFlush(d);nap();
 }
 if(hud)XDestroyWindow(d,hud);
 if(gc)XFreeGC(d,gc);
 if(font)XFreeFont(d,font);
 XCloseDisplay(d);return 0;
}
