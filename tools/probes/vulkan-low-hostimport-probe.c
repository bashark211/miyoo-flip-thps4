#include <vulkan/vulkan.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#define CHECK(x) do{VkResult z=(x);if(z!=VK_SUCCESS){printf("FAIL %s = %d\n",#x,z);return 2;}}while(0)
int main(void){
 setbuf(stdout,NULL);
 VkApplicationInfo ai={.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO,.pApplicationName="Flip lowmap probe",.apiVersion=VK_API_VERSION_1_1};
 VkInstanceCreateInfo ii={.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,.pApplicationInfo=&ai};VkInstance in;CHECK(vkCreateInstance(&ii,NULL,&in));
 uint32_t np=0;CHECK(vkEnumeratePhysicalDevices(in,&np,NULL));if(!np){puts("FAIL no GPU");return 3;}VkPhysicalDevice *ps=calloc(np,sizeof(*ps));CHECK(vkEnumeratePhysicalDevices(in,&np,ps));VkPhysicalDevice gpu=ps[0];free(ps);
 VkPhysicalDeviceProperties props;vkGetPhysicalDeviceProperties(gpu,&props);printf("GPU %s\n",props.deviceName);
 uint32_t nq=0;vkGetPhysicalDeviceQueueFamilyProperties(gpu,&nq,NULL);VkQueueFamilyProperties *qs=calloc(nq,sizeof(*qs));vkGetPhysicalDeviceQueueFamilyProperties(gpu,&nq,qs);uint32_t q=0;while(q<nq && !(qs[q].queueFlags&VK_QUEUE_GRAPHICS_BIT))q++;free(qs);if(q==nq)return 4;
 float pri=0;VkDeviceQueueCreateInfo qi={.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,.queueFamilyIndex=q,.queueCount=1,.pQueuePriorities=&pri};VkDeviceCreateInfo di={.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,.queueCreateInfoCount=1,.pQueueCreateInfos=&qi};const char* ext=VK_EXT_EXTERNAL_MEMORY_HOST_EXTENSION_NAME;di.enabledExtensionCount=1;di.ppEnabledExtensionNames=&ext;VkDevice d;CHECK(vkCreateDevice(gpu,&di,NULL,&d));VkQueue queue;vkGetDeviceQueue(d,q,0,&queue);
 VkPhysicalDeviceMemoryProperties mp;vkGetPhysicalDeviceMemoryProperties(gpu,&mp);
 const VkDeviceSize bytes=65536;VkBuffer b[2];VkDeviceMemory m[2];void *p[2];int low=1;VkDeviceSize host_sizes[2];PFN_vkGetMemoryHostPointerPropertiesEXT hostprops=(PFN_vkGetMemoryHostPointerPropertiesEXT)vkGetDeviceProcAddr(d,"vkGetMemoryHostPointerPropertiesEXT");if(!hostprops)return 7;
 for(int k=0;k<2;k++){
  VkBufferCreateInfo bi={.sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,.size=bytes,.usage=VK_BUFFER_USAGE_TRANSFER_SRC_BIT|VK_BUFFER_USAGE_TRANSFER_DST_BIT,.sharingMode=VK_SHARING_MODE_EXCLUSIVE};VkExternalMemoryBufferCreateInfo ex={.sType=VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_BUFFER_CREATE_INFO,.handleTypes=VK_EXTERNAL_MEMORY_HANDLE_TYPE_HOST_ALLOCATION_BIT_EXT};bi.pNext=&ex;CHECK(vkCreateBuffer(d,&bi,NULL,&b[k]));VkMemoryRequirements mr;vkGetBufferMemoryRequirements(d,b[k],&mr);uint32_t t=0;host_sizes[k]=(mr.size+4095)&~(VkDeviceSize)4095;void* host=mmap((void*)(uintptr_t)(0x10000000u+k*0x1000000u),host_sizes[k],PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);if(host==MAP_FAILED){perror("host mmap");return 8;}VkMemoryHostPointerPropertiesEXT hp={.sType=VK_STRUCTURE_TYPE_MEMORY_HOST_POINTER_PROPERTIES_EXT};CHECK(hostprops(d,VK_EXTERNAL_MEMORY_HANDLE_TYPE_HOST_ALLOCATION_BIT_EXT,host,&hp));printf("HOST_TYPES %x req=%x\n",hp.memoryTypeBits,mr.memoryTypeBits);mr.memoryTypeBits &= hp.memoryTypeBits;
  while(t<mp.memoryTypeCount && (!(mr.memoryTypeBits&(1u<<t)) || (mp.memoryTypes[t].propertyFlags&(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))!=(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)))t++;
  if(t==mp.memoryTypeCount){puts("FAIL no coherent host memory");return 5;}
  VkMemoryAllocateInfo ma={.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,.allocationSize=mr.size,.memoryTypeIndex=t};VkImportMemoryHostPointerInfoEXT hi={.sType=VK_STRUCTURE_TYPE_IMPORT_MEMORY_HOST_POINTER_INFO_EXT,.handleType=VK_EXTERNAL_MEMORY_HANDLE_TYPE_HOST_ALLOCATION_BIT_EXT,.pHostPointer=host};ma.pNext=&hi;CHECK(vkAllocateMemory(d,&ma,NULL,&m[k]));CHECK(vkBindBufferMemory(d,b[k],m[k],0));void* real=NULL;CHECK(vkMapMemory(d,m[k],0,VK_WHOLE_SIZE,0,&real));p[k]=host;printf("DRIVER_MAP %p HOST_ALIAS %p\n",real,host);printf("MAP %d ptr=%p flags=0x%x low32=%d\n",k,p[k],mp.memoryTypes[t].propertyFlags,(uintptr_t)p[k]<=UINT32_MAX);if((uintptr_t)p[k]>UINT32_MAX)low=0;
 }
 for(uint32_t j=0;j<bytes/4;j++){((uint32_t*)p[0])[j]=j*2654435761u+0x51a70000u;((uint32_t*)p[1])[j]=0;}
 VkMappedMemoryRange ranges[2]={{.sType=VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE,.memory=m[0],.offset=0,.size=VK_WHOLE_SIZE},{.sType=VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE,.memory=m[1],.offset=0,.size=VK_WHOLE_SIZE}};
#ifndef COHERENT_ONLY
 CHECK(vkFlushMappedMemoryRanges(d,2,ranges));
#endif

 VkCommandPoolCreateInfo ci={.sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,.queueFamilyIndex=q};VkCommandPool pool;CHECK(vkCreateCommandPool(d,&ci,NULL,&pool));VkCommandBufferAllocateInfo ca={.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,.commandPool=pool,.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,.commandBufferCount=1};VkCommandBuffer c;CHECK(vkAllocateCommandBuffers(d,&ca,&c));VkCommandBufferBeginInfo cb={.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};CHECK(vkBeginCommandBuffer(c,&cb));VkBufferCopy copy={.size=bytes};vkCmdCopyBuffer(c,b[0],b[1],1,&copy);
 VkMemoryBarrier barrier={.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER,.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT,.dstAccessMask=VK_ACCESS_HOST_READ_BIT};vkCmdPipelineBarrier(c,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,1,&barrier,0,NULL,0,NULL);CHECK(vkEndCommandBuffer(c));VkSubmitInfo si={.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO,.commandBufferCount=1,.pCommandBuffers=&c};CHECK(vkQueueSubmit(queue,1,&si,VK_NULL_HANDLE));CHECK(vkQueueWaitIdle(queue));
#ifndef COHERENT_ONLY
 CHECK(vkInvalidateMappedMemoryRanges(d,1,&ranges[1]));
#endif

 for(uint32_t j=0;j<bytes/4;j++)if(((uint32_t*)p[1])[j]!=j*2654435761u+0x51a70000u){printf("FAIL GPU copy word=%u value=%x\n",j,((uint32_t*)p[1])[j]);return 6;}
 puts("GPU_COPY_PASS bytes=65536");printf("LOW32_RESULT %s\n",low?"PASS":"HIGH_POINTERS");
 vkDestroyCommandPool(d,pool,NULL);for(int k=0;k<2;k++){vkUnmapMemory(d,m[k]);vkDestroyBuffer(d,b[k],NULL);vkFreeMemory(d,m[k],NULL);munmap(p[k],host_sizes[k]);}vkDestroyDevice(d,NULL);vkDestroyInstance(in,NULL);return 0;
}
