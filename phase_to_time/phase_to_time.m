fc=1e7; % carrier frequency
N=100;  % interpolation factor
% phase noise spectral SdBc @ fF
fF=  [1    10  100 1000 10000 1e5] %  1e6  1e7];
SdBc=[-70 -70  -95 -120 -130 -130] % -130 -130]

%%%%%%%% interpolate, convert SdBc to SdBrad & integrate over bandwidth bins
SdBcint=[];
fFint=[];
for k=1:length(SdBc)-1
   SdBcint=[SdBcint SdBc(k)+(SdBc(k+1)-SdBc(k))/(fF(k+1)-fF(k))*(linspace((fF(k)),(fF(k+1)),N)-fF(k))];
   fFint=[fFint logspace(log10(fF(k)),log10(fF(k+1)),N)];
end

SdBrad=SdBcint+3;   % dBc/Hz -> dBrad^2/Hz
rad=sqrt(10.^(SdBrad(1:end-1)/10).*(fFint(2:end)-fFint(1:end-1))); % dBrad^2/Hz -> rad
res=rad/2/pi/fc;    % rad -> s
sqrt(sum(res.^2))   % integrate noise fluctuations
semilogx(fFint,(SdBcint))
xlabel('Fourier frequency (Hz)')
ylabel('Phase noise (dBc/Hz)')
