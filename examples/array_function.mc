{
    int sum(int n){
        int[100] arr;
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
        int res = sum(read_int());
        print_int(res);
        return 0;
    }
}
