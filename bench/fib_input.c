
int fib(int n) {
	if(n<2) return 1;
	return fib(n-1) + fib(n-2);
}	

void main() {
	int i = read_int();
	start_measurement();
	int res = fib(i);
	end_measurement();
	print_int(res);
}
	
