{
    int main(){
        int i;
        int size = read_int();
        int[size] a;
        int[size] b;
        int[size] c;
        for(i=0;i<size;i=i+1){
            a[i] = i;
            b[i] = size-i;
        }
        for(i=0;i<size;i=i+1){
            c[i] = a[i]*b[i];
        }
        int sum = 0;
        for(i=0;i<size;i=i+1){
            sum = sum + c[i];
        }
        print_int(sum);
        return 0;
    }
}
