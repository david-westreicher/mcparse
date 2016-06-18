
int fib(int n) {
	if(n<2) return 1;
	return fib(n-1) + fib(n-2);
}	

void main() {	
	start_measurement();
	int res = fib(15);
	end_measurement();
	print_int(res);
}
	
