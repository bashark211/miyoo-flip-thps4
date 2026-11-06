.section .text
.global _start
_start:
 call main
 mov %eax,%ebx
 mov $1,%eax
 int $0x80
.balign 16
.global wine_memmove
.type wine_memmove,@function
wine_memmove:
.incbin "wine821-sse2-memmove.bin"
.size wine_memmove,.-wine_memmove
.section .note.GNU-stack,"",@progbits
