fc=1e7; % carrier frequency
N=100;  % interpolation factor
% phase noise spectral SdBc @ fF
fF=  [1    10  100 1000 10000 1e5] %  1e6  1e7];
SdBc=[-70 -70  -95 -120 -130 -130] % -130 -130]

%%%%%%%% interpolate, convert SdBc to SdBrad to Sy (linear) & integrate to AVAR
SdBcint=[];
fFint=[];
for k=1:length(SdBc)-1
   SdBcint=[SdBcint SdBc(k)+(SdBc(k+1)-SdBc(k))/(fF(k+1)-fF(k))*(linspace((fF(k)),(fF(k+1)),N)-fF(k))];
   fFint=[fFint logspace(log10(fF(k)),log10(fF(k+1)),N)];
end

subplot(211)
SdBrad=SdBcint+3;   % dBc/Hz -> dBrad^2/Hz
Sy=(10.^(SdBrad/10)).*(fFint.^2);
semilogx(fFint,10*log10(Sy))
hold on
semilogx(fFint,(SdBrad))
xlabel('Fourier frequency (Hz)')
ylabel('Phase noise (dBc/Hz)')
subplot(212)
m=1
for tau=logspace(-2,5,1024)
  avar(m)=2*sum(Sy(1:end-1).*(fFint(2:end)-fFint(1:end-1)).*sin(4*pi*tau*fFint(1:end-1)).^4./(4*pi*tau*fFint(1:end-1)).^2);
  m=m+1;
end

% plot resulting adev=sqrt(avar)
adev=sqrt(avar);
loglog(logspace(-2,2,1024),adev/fc)
