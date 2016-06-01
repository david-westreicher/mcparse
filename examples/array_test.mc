{
    int main(){
        int i;
        int[5] a;
        int[5] b;
        int[5] c;
        for(i=0;i<5;i=i+1){
            a[i] = read_int();
            b[i] = read_int();
        }
        for(i=0;i<5;i=i+1){
            c[i] = a[i]*b[i];
        }
        int sum = 0;
        for(i=0;i<5;i=i+1){
            sum = sum + c[i];
        }
        print_int(sum);
        return 0;
    }
}
