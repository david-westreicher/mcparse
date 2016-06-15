{
    int[20] a;
    int[20] b;
    int[20] c;
    a[0] = 10;
    for(int i = 0; i< 20;i=i+1){
        for(int j = 0; j< 20;j=j+1){
            b[i+0] = a[i+0];
            a[i+1] = b[i+1];
            a[i+2] = b[i+2];
        }
    }
}
