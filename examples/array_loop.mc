{
    int main(){
        int[100] arr;
        int setnums = read_int();
        for(int i =0;i<setnums;i=i+1){
            arr[i] = i;
        }
        for(i =0;i<setnums;i=i+1){
            print_int(arr[i]);
        }
        return 0;
    }
}
