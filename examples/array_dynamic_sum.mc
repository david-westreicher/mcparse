{
    int sum(int n){
        int[n] arr;
        for(int i=0;i<n;i=i+1){
            arr[i] = i;
        }
        int sum = 0;
        for(i=0;i<n;i=i+1){
            sum = sum + arr[i];
        }
        return sum;
    }
    int main(){
        print_int(sum(read_int()));
        return 0;
    }
}
