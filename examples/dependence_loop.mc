{
    int[20] a;
    for(int i = 0; i< 20;i=i+1){
        for(int j = 0; j< 20;j=j+1){
            a[i+2] = a[i];
            a[4] = a[3];
        }
    }
}
