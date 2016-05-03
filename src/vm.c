#include <stdio.h>


int main(){
    int memnum;
    int codenum;
    scanf("%d %d", &memnum, &codenum);
    int mem[memnum];
    char names[memnum][100];
    for(int i =0;i<memnum;i++){
        int val;
        scanf("%99s %d", &names[i], &val);
        mem[i] = val;
    }
    int code[codenum][4];
    for(int i=0;i<codenum;i++){
        int op;
        int arg1;
        int arg2;
        int res;
        scanf("%d %d %d %d", &op, &arg1, &arg2, &res);
        code[i][0] = op;
        code[i][1] = arg1;
        code[i][2] = arg2;
        code[i][3] = res;
    }
    /*
        for(int i =0;i<memnum;i++){
            printf("%d\n", mem[i]);
        }
        for(int i=0;i<codenum;i++){
            printf("code: %d %d %d %d\n", code[i][0], code[i][1], code[i][2], code[i][3]);
        }
    */

    int pc = 0;
    int end = codenum-1;
    while(pc<=end){
        int op = code[pc][0];
        int arg1 = code[pc][1];
        int arg2 = code[pc][2];
        int result = code[pc][3];
        int skip = 0;
        switch(op){
            case 0:
                mem[result] = mem[arg1];
                break;
            case 1:
                pc = result;
                skip = 1;
                break;
            case 2:
                if(!mem[arg1]){
                    pc = result;
                    skip = 1;
                }
                break;
            case 3:
                mem[result] = mem[arg1] <= mem[arg2];
                break;
            case 4:
                mem[result] = mem[arg1] >= mem[arg2];
                break;
            case 5:
                mem[result] = mem[arg1] == mem[arg2];
                break;
            case 6:
                mem[result] = mem[arg1] != mem[arg2];
                break;
            case 7:
                mem[result] = mem[arg1] < mem[arg2];
                break;
            case 8:
                mem[result] = mem[arg1] > mem[arg2];
                break;
            case 9:
                mem[result] = mem[arg1] + mem[arg2];
                break;
            case 10:
                mem[result] = mem[arg1] - mem[arg2];
                break;
            case 11:
                mem[result] = mem[arg1] * mem[arg2];
                break;
            case 12:
                mem[result] = mem[arg1] / mem[arg2];
                break;
            case 13:
                mem[result] = mem[arg1] % mem[arg2];
                break;
            case 14:
                mem[result] = -mem[arg1];
                break;
            case 15:
                mem[result] = !mem[arg1];
                break;
        }
        if(!skip)
            pc++;
    }
    for(int i =0;i<memnum;i++){
        printf("%s: \t%d\n", names[i], mem[i]);
    }
}
