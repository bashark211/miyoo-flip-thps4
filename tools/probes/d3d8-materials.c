#define COBJMACROS
#include <windows.h>
#include <d3d8.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct { float x,y,z,rhw; DWORD colour; float u,v; } Vertex;
static LRESULT CALLBACK proc(HWND w,UINT m,WPARAM a,LPARAM b) {
    return DefWindowProcA(w,m,a,b);
}
static int near_colour(DWORD pixel,DWORD expected) {
    for(int shift=0;shift<24;shift+=8)
        if(abs((int)((pixel>>shift)&255)-(int)((expected>>shift)&255))>4) return 0;
    return 1;
}
static IDirect3DTexture8* texture(IDirect3DDevice8* dev,D3DFORMAT format,DWORD a,DWORD b) {
    IDirect3DTexture8* out=NULL;
    HRESULT hr=IDirect3DDevice8_CreateTexture(dev,2,1,1,0,format,D3DPOOL_MANAGED,&out);
    if(FAILED(hr)) { printf("Texture create format=%u failed=%08lx\n",format,(unsigned long)hr); return NULL; }
    D3DLOCKED_RECT lock;
    if(FAILED(IDirect3DTexture8_LockRect(out,0,&lock,NULL,0))) return NULL;
    if(format==D3DFMT_A1R5G5B5) { ((WORD*)lock.pBits)[0]=a; ((WORD*)lock.pBits)[1]=b; }
    else { ((DWORD*)lock.pBits)[0]=a; ((DWORD*)lock.pBits)[1]=b; }
    IDirect3DTexture8_UnlockRect(out,0);
    return out;
}
static IDirect3DTexture8* bc3_red(IDirect3DDevice8* dev) {
 IDirect3DTexture8* out=NULL;
 HRESULT hr=IDirect3DDevice8_CreateTexture(dev,16,16,3,0,D3DFMT_DXT5,D3DPOOL_MANAGED,&out);
 printf("BC3 16x16 three-mip allocation=%08lx\n",(unsigned long)hr);fflush(stdout);
 if(FAILED(hr))return NULL;
 const unsigned char block[16]={128,0,0,0,0,0,0,0,0,248,0,0,0,0,0,0};
 for(unsigned mip=0;mip<3;mip++){
  D3DLOCKED_RECT lock;hr=IDirect3DTexture8_LockRect(out,mip,&lock,NULL,0);
  if(FAILED(hr))return NULL;
  unsigned blocks=((16>>mip)+3)/4;
  for(unsigned y=0;y<blocks;y++)for(unsigned x=0;x<blocks;x++)memcpy((char*)lock.pBits+y*lock.Pitch+x*16,block,16);
  IDirect3DTexture8_UnlockRect(out,mip);
 }
 return out;
}
int WINAPI WinMain(HINSTANCE instance,HINSTANCE previous,LPSTR command,int show) {
    WNDCLASSA wc={0};wc.lpfnWndProc=proc;wc.hInstance=instance;wc.lpszClassName="MaterialDiagnostic";
    RegisterClassA(&wc);
    HWND window=CreateWindowA(wc.lpszClassName,"Material diagnostic",WS_OVERLAPPEDWINDOW,0,0,640,480,NULL,NULL,instance,NULL);
    ShowWindow(window,SW_SHOW);
    IDirect3D8* d3d=Direct3DCreate8(D3D_SDK_VERSION);
    if(!d3d) return 2;
    D3DDISPLAYMODE mode;IDirect3D8_GetAdapterDisplayMode(d3d,0,&mode);
    D3DPRESENT_PARAMETERS pp={0};pp.Windowed=TRUE;pp.BackBufferWidth=640;pp.BackBufferHeight=480;
    pp.BackBufferFormat=mode.Format;pp.BackBufferCount=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
    pp.EnableAutoDepthStencil=TRUE;pp.AutoDepthStencilFormat=D3DFMT_D16;pp.Flags=D3DPRESENTFLAG_LOCKABLE_BACKBUFFER;pp.hDeviceWindow=window;
    IDirect3DDevice8* dev=NULL;
    HRESULT hr=IDirect3D8_CreateDevice(d3d,0,D3DDEVTYPE_HAL,window,D3DCREATE_SOFTWARE_VERTEXPROCESSING,&pp,&dev);
    if(FAILED(hr)) { printf("CreateDevice=%08lx\n",(unsigned long)hr); return 2; }
    IDirect3DTexture8* red=bc3_red(dev);
    IDirect3DTexture8* grey=texture(dev,D3DFMT_A8R8G8B8,0xff404040,0xff404040);
    IDirect3DTexture8* mask=texture(dev,D3DFMT_A1R5G5B5,0x7c00,0xfc00);
    if(!red || !grey || !mask) return 2;
    IDirect3DDevice8_SetRenderState(dev,D3DRS_LIGHTING,FALSE);
    IDirect3DDevice8_SetRenderState(dev,D3DRS_ZENABLE,FALSE);
    IDirect3DDevice8_SetRenderState(dev,D3DRS_CULLMODE,D3DCULL_NONE);
    IDirect3DDevice8_SetVertexShader(dev,D3DFVF_XYZRHW|D3DFVF_DIFFUSE|D3DFVF_TEX1);
    const char* names[]={"alpha-modulate","colour-modulate2x","font-alpha-mask","two-stage-lightmap","font-alpha-modulate2x-depth","font-alpha-modulate2x-no-depth"};
    const DWORD expected_left[]={0x4000bf,0x404040,0x0000ff,0x800000,0x80007f,0x80007f};
    const DWORD expected_right[]={0x4000bf,0x404040,0xff0000,0x800000,0x80007f,0x80007f};
    int passed=0;
    for(int test=0;test<6;test++) {
        DWORD colour=test>=4?0x80808080:test==0?0x80ffffff:test==1?0xff808080:0xffffffff;
        Vertex quad[]={{100,80,.5f,1,colour,0,0},{540,80,.5f,1,colour,1,0},
            {100,400,.5f,1,colour,0,1},{540,400,.5f,1,colour,1,1}};
        IDirect3DDevice8_SetTexture(dev,0,(IDirect3DBaseTexture8*)(test==1?grey:test==2?mask:red));
        IDirect3DDevice8_SetTextureStageState(dev,0,D3DTSS_COLOROP,(test==1||test>=4)?D3DTOP_MODULATE2X:D3DTOP_MODULATE);
        IDirect3DDevice8_SetTextureStageState(dev,0,D3DTSS_COLORARG1,D3DTA_TEXTURE);
        IDirect3DDevice8_SetTextureStageState(dev,0,D3DTSS_COLORARG2,D3DTA_DIFFUSE);
        IDirect3DDevice8_SetTextureStageState(dev,0,D3DTSS_ALPHAOP,test>=4?D3DTOP_MODULATE2X:test==0?D3DTOP_MODULATE:D3DTOP_SELECTARG1);
        IDirect3DDevice8_SetTextureStageState(dev,0,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);
        IDirect3DDevice8_SetTextureStageState(dev,0,D3DTSS_ALPHAARG2,D3DTA_DIFFUSE);
        IDirect3DDevice8_SetTextureStageState(dev,1,D3DTSS_COLOROP,D3DTOP_DISABLE);
        IDirect3DDevice8_SetTextureStageState(dev,1,D3DTSS_ALPHAOP,D3DTOP_DISABLE);
        IDirect3DDevice8_SetTexture(dev,1,NULL);
        if(test==3) {
            IDirect3DDevice8_SetTexture(dev,1,(IDirect3DBaseTexture8*)grey);
            IDirect3DDevice8_SetTextureStageState(dev,1,D3DTSS_TEXCOORDINDEX,0);
            IDirect3DDevice8_SetTextureStageState(dev,1,D3DTSS_COLOROP,D3DTOP_MODULATE2X);
            IDirect3DDevice8_SetTextureStageState(dev,1,D3DTSS_COLORARG1,D3DTA_TEXTURE);
            IDirect3DDevice8_SetTextureStageState(dev,1,D3DTSS_COLORARG2,D3DTA_CURRENT);
            IDirect3DDevice8_SetTextureStageState(dev,1,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);
            IDirect3DDevice8_SetTextureStageState(dev,1,D3DTSS_ALPHAARG1,D3DTA_CURRENT);
        }
        for(int stage=0;stage<2;stage++) {
            IDirect3DDevice8_SetTextureStageState(dev,stage,D3DTSS_MINFILTER,D3DTEXF_POINT);
            IDirect3DDevice8_SetTextureStageState(dev,stage,D3DTSS_MAGFILTER,D3DTEXF_POINT);
            IDirect3DDevice8_SetTextureStageState(dev,stage,D3DTSS_MIPFILTER,D3DTEXF_NONE);
        }
        IDirect3DDevice8_SetRenderState(dev,D3DRS_ALPHABLENDENABLE,test==0 || test>=4);
        IDirect3DDevice8_SetRenderState(dev,D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);
        IDirect3DDevice8_SetRenderState(dev,D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
        IDirect3DDevice8_SetRenderState(dev,D3DRS_ALPHATESTENABLE,test==2 || test>=4);
        IDirect3DDevice8_SetRenderState(dev,D3DRS_ALPHAFUNC,test>=4?D3DCMP_GREATEREQUAL:D3DCMP_GREATER);
        IDirect3DDevice8_SetRenderState(dev,D3DRS_ALPHAREF,test>=4?1:128);
        IDirect3DDevice8_SetRenderState(dev,D3DRS_ZENABLE,test==4);
        if(test>=4)for(int i=0;i<4;i++)quad[i].z=0;
        for(int frame=0;frame<20;frame++) {
            MSG msg;while(PeekMessageA(&msg,NULL,0,0,PM_REMOVE)) { TranslateMessage(&msg);DispatchMessageA(&msg); }
            IDirect3DDevice8_Clear(dev,0,NULL,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff0000ff,1,0);
            IDirect3DDevice8_BeginScene(dev);
            IDirect3DDevice8_DrawPrimitiveUP(dev,D3DPT_TRIANGLESTRIP,2,quad,sizeof(Vertex));
            IDirect3DDevice8_EndScene(dev);
            if(frame==19) {
                IDirect3DSurface8* surface=NULL;D3DLOCKED_RECT lock;
                IDirect3DDevice8_GetBackBuffer(dev,0,D3DBACKBUFFER_TYPE_MONO,&surface);
                hr=IDirect3DSurface8_LockRect(surface,&lock,NULL,D3DLOCK_READONLY);
                if(SUCCEEDED(hr)) {
                    DWORD left=*(DWORD*)((char*)lock.pBits+240*lock.Pitch+210*4);
                    DWORD right=*(DWORD*)((char*)lock.pBits+240*lock.Pitch+430*4);
                    int ok=near_colour(left,expected_left[test]) && near_colour(right,expected_right[test]);
                    printf("MATERIAL %s: %s pixels=%08lx,%08lx expected=%06lx,%06lx\n",names[test],ok?"PASS":"FAIL",
                        (unsigned long)left,(unsigned long)right,(unsigned long)expected_left[test],(unsigned long)expected_right[test]);
                    passed+=ok;
                    IDirect3DSurface8_UnlockRect(surface);
                } else printf("MATERIAL %s: LOCK FAILED %08lx\n",names[test],(unsigned long)hr);
                IDirect3DSurface8_Release(surface);fflush(stdout);
            }
            IDirect3DDevice8_Present(dev,NULL,NULL,NULL,NULL);Sleep(16);
        }
    }
    printf("MATERIAL TOTAL: %d/6\n",passed);fflush(stdout);
    IDirect3DTexture8_Release(red);IDirect3DTexture8_Release(grey);IDirect3DTexture8_Release(mask);
    IDirect3DDevice8_Release(dev);IDirect3D8_Release(d3d);DestroyWindow(window);
    return passed==6?0:3;
}
