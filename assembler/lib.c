#include <stdio.h>

int read_int();
float read_float();
void print_int(int out);
void print_float(float out);

int read_int() {
	int ret = 0;
	printf("Enter an integer: ");
	scanf("%d", &ret);
	return ret;
}

float read_float() {
	float ret = 0.0f;
	printf("Enter a floating point number: ");
	scanf("%f", &ret);
	return ret;
}

void print_int(int out) {
	printf("%8d\n", out);
}

void print_float(float out) {
	printf("%8.4f\n", out);
}
