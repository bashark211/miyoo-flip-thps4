/* Standalone i386 correctness/performance probe; no Wine prefix or game files. */
typedef unsigned int u32;
extern void *wine_memmove(void *,const void *,u32);
static unsigned char actual[32768],expected[32768],source[1048640],dest[1048640];
static int sys3(int n,int a,int b,int c){int r;__asm__ volatile("int $0x80":"=a"(r):"a"(n),"b"(a),"c"(b),"d"(c):"memory");return r;}
static void out(const char*s){u32 n=0;while(s[n])n++;sys3(4,1,(int)s,n);}
static void number(u32 n){char s[12];int i=11;s[i]=0;do{s[--i]='0'+n%10;n/=10;}while(n);out(s+i);}
static u32 ticks(void){u32 t[2]={0};if(sys3(265,1,(int)t,0))return 0;return t[0]*1000+t[1]/1000000;}
static void refmove(unsigned char*d,const unsigned char*s,u32 n){if(d>s && d<s+n){while(n){--n;d[n]=s[n];}}else{for(u32 i=0;i<n;i++)d[i]=s[i];}}
int main(void){
 u32 lengths[]={0,1,2,3,4,7,8,15,16,31,32,63,64,65,255,256,511,1024,4095,4096};int shifts[]={-65,-16,-7,-1,0,1,7,16,65,8192};u32 tests=0;
 if(wine_memmove((void*)0,(void*)0,0)!=(void*)0){out("FAIL null zero\n");return 2;}
 for(u32 n=0;n<20;n++)for(u32 align=0;align<16;align++)for(u32 j=0;j<10;j++){
  for(u32 i=0;i<32768;i++)actual[i]=expected[i]=(unsigned char)(i*73u+19u);
  u32 src=1024+align, dst=src+shifts[j];refmove(expected+dst,expected+src,lengths[n]);
  if(wine_memmove(actual+dst,actual+src,lengths[n])!=actual+dst){out("FAIL return\n");return 3;}
  for(u32 i=0;i<32768;i++)if(actual[i]!=expected[i]){out("FAIL data n=");number(lengths[n]);out(" offset=");number(j);out("\n");return 4;}
  tests++;
 }
 out("CORRECTNESS_PASS cases=");number(tests);out("\n");
 for(u32 i=0;i<1048640;i++)source[i]=(unsigned char)(i*31u+3u);
 u32 sizes[]={1024,16384,262144,1048576};
 for(u32 k=0;k<4;k++)for(u32 align=0;align<2;align++){
  u32 n=sizes[k],count=33554432u/n;for(u32 w=0;w<32;w++)wine_memmove(dest,source+align,n);
  u32 start=ticks();for(u32 i=0;i<count;i++)wine_memmove(dest,source+align,n);u32 elapsed=ticks()-start;
  for(u32 i=0;i<n;i++)if(dest[i]!=source[i+align])return 5;
  out("COPY bytes=");number(n);out(" src_misaligned=");number(align);out(" total_bytes=");number(n*count);out(" elapsed_ms=");number(elapsed);out("\n");
 }
 return 0;
}
