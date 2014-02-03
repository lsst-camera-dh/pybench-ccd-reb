#include <stdio.h>
#include <math.h>
#include <stdlib.h>

#define BUFSIZE 128
char buffer[BUFSIZE];


long int chunk_analysis(FILE *f,
			long int pos, // last line read
			long int start, // should have: start > pos
			long int stop,
			double *mean,
			double *var,
			long int *n) {
  // will return the line number of the last line read
  double sum, sum2;
  long int value;
  long int k;

  k = 0;
  while ((pos + k) < start) {
    fgets(buffer, BUFSIZE-1, f);
    if (feof(f)) {
      printf("ARGHHHHHHH\n");
      return -1;
    }
    if ((buffer[0] == '#')  || 
	(buffer[0] == '\0') || 
	(buffer[0] == '\n') || 
	(buffer[0] == '\r')) {
      continue;
    }
    k++;
  }

  *n = 0;
  sum = sum2 = 0.0;
  while ((pos + k) < stop) {
    fgets(buffer, BUFSIZE-1, f);
    if (feof(f)) {
      printf("ARGHHHHHHH\n");
      return -1;
    }
    if ((buffer[0] == '#')  || 
	(buffer[0] == '\0') || 
	(buffer[0] == '\n') || 
	(buffer[0] == '\r')) {
      continue;
    }
    value = atoi(buffer);
    // printf("[%ld]\n", value);
    sum += value;
    sum2 += value*value;
    k++;
    (*n)++;
  }

  // printf("n = %ld\n", *n);
  // printf("Mean = %g\n", A);
  // printf("s^2_n = %g\n", Q / (n - 1));
  // printf("sigma^2_n = %g\n", Q / n);
  *mean = sum / *n;
  *var = sum2 / *n - *mean * *mean;
  // printf("Mean = %g\n", *mean);
  // printf("s^2_n = %g\n", *var);
  // printf("sigma^2_n = %g\n", *var * n / (double)(n - 1));
  
  return (pos + k);
}

long int pulse_analysis(FILE *f, 
			//
			long int before_start,
			long int before_stop,
			double *before_mean,
			double *before_var,
			long int *before_n,
			//
			long int in_start,
			long int in_stop,
			double *in_mean,
			double *in_var,
			long int *in_n,
			//
			long int after_start,
			long int after_stop,
			double *after_mean,
			double *after_var,
			long int *after_n) {
  
  long int pos;

  pos = chunk_analysis(f, 0, 
		       before_start, before_stop,
		       before_mean, before_var, before_n);
  if (pos < 0) return -1;

  pos = chunk_analysis(f, pos, 
		       in_start, in_stop,
		       in_mean, in_var, in_n);
  if (pos < 0) return -1;

  pos = chunk_analysis(f, pos, 
		       after_start, after_stop,
		       after_mean, after_var, after_n);
  if (pos < 0) return -1;

  return pos;
}


// int main(int argc, char *argv[]) {
  
//   FILE *f;
//   char buffer[BUFSIZE];

//   f = fopen("test.data", "r");
//   double bf_mean, bf_var, in_mean, in_var, af_mean, af_var;
//   int m = 1;
//   pulse_analysis(f,
// 		 0+m,  10-m, &bf_mean, &bf_var,
// 		 10+m, 30-m, &in_mean, &in_var,
// 		 30+m, 40-m, &af_mean, &af_var);
//   fclose(f);

//   printf("Before -----------------------------------------------------\n");
//   printf("Mean = %g\n", bf_mean);
//   printf("s^2_n = %g\t sqrt(s^2_n) = %g\n", bf_var, sqrt(bf_var));
//   printf("Pulse ------------------------------------------------------\n");
//   printf("Mean = %g\n", in_mean);
//   printf("s^2_n = %g\t sqrt(s^2_n) = %g\n", in_var, sqrt(in_var));
//   printf("After ------------------------------------------------------\n");
//   printf("Mean = %g\n", af_mean);
//   printf("s^2_n = %g\t sqrt(s^2_n) = %g\n", af_var, sqrt(af_var));
//   printf("------------------------------------------------------------\n");

//   return 0;
// }
