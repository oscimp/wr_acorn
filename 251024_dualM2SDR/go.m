fs=8;
f=fopen('0.bin'); d=fread(f,inf,'int16');d=d(1:2:end)+j*d(2:2:end);d11=d(1:2:end);d21=d(2:2:end);
f=fopen('2.bin'); d=fread(f,inf,'int16');d=d(1:2:end)+j*d(2:2:end);d12=d(1:2:end);d22=d(2:2:end);
fr=linspace(-fs/2,fs/2,length(d11));
subplot(221);plot(fr,abs(fftshift(fft(d11))));hold on;plot(fr,abs(fftshift(fft(d21))));xlabel('f (MHz)');ylabel('|FFT|');legend('ch1','ch2')
subplot(222);plot(fr,abs(fftshift(fft(d12))));hold on;plot(fr,abs(fftshift(fft(d22))));xlabel('f (MHz)');ylabel('|FFT|');legend('ch1','ch2')
subplot(212)
plot([0:length(d11)-1]/fs/1e6,arg(d11./d12));
hold on

f=fopen('0_ext.bin'); d=fread(f,inf,'int16');d=d(1:2:end)+j*d(2:2:end);d11=d(1:2:end);d21=d(2:2:end);
f=fopen('2_ext.bin'); d=fread(f,inf,'int16');d=d(1:2:end)+j*d(2:2:end);d12=d(1:2:end);d22=d(2:2:end);
subplot(212)
plot([0:length(d11)-1]/fs/1e6,arg(d11./d12));xlabel('time (s)');
legend('internal','external (WR)')
