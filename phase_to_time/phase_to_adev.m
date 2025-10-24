fc=1e7; % carrier frequency
N=100;  % interpolation factor
% phase noise spectral SdBc @ fF
fF=  [1    10  100 1000 10000 1e5 1e6 1e7] % extend 100 kHz measurement floor to 10 MHz
SdBc(:,1)=[-70  -70  -95  -120 -130 -130 -130 -130]; % BC/GM class I
SdBc(:,2)=[-100 -100 -115 -130 -140 -140 -140 -140]; % GM class II (LJ)
SdBc(:,3)=[-90  -90  -107 -125 -135 -135 -135 -135]  % BC class II



%%%%%%%% interpolate, convert SdBc to SdBrad to Sy (linear) & integrate to AVAR
for count=1:3
  SdBcint=[];
  fFint=[];
  for k=1:length(SdBc(:,count))-1
     SdBcint=[SdBcint SdBc(k,count)+(SdBc(k+1,count)-SdBc(k,count))/(fF(k+1)-fF(k))*(linspace((fF(k)),(fF(k+1)),N)-fF(k))];
     fFint=[fFint logspace(log10(fF(k)),log10(fF(k+1)),N)];
  end

  SdBrad=SdBcint+3;   % dBc/Hz -> dBrad^2/Hz
  Sy=(10.^(SdBrad/10)).*(fFint.^2);
  if (count==1)
    figure(1)
    subplot(211)
    semilogx(fFint,(SdBrad))
    hold on
    semilogx(fFint,10*log10(Sy))
    xlabel('Fourier frequency (Hz)')
    ylabel('phase noise (dBc/Hz)');legend('Sphi','Sy=Sphixf^2','location','southwest')
    grid on
    title('Class I')
  end
  m=1;
  for tau=logspace(-2,2,1024)
% see https://rubiola.org/pdf-lectures/Scientific%20Instruments%20L06-10,%20Oscillators.pdf
% slide 49
    avar(m)=2*sum(Sy(1:end-1).*(fFint(2:end)-fFint(1:end-1)).*sin(pi*tau*fFint(1:end-1)).^4./(pi*tau*fFint(1:end-1)).^2);
% slide 51
    mvar(m)=2*sum(Sy(1:end-1).*(fFint(2:end)-fFint(1:end-1)).*sin(pi*tau*fFint(1:end-1)).^6./(pi*tau*fFint(1:end-1)).^4);
    m=m+1;
  end
  figure(99)
  subplot(211)
  % plot resulting adev=sqrt(avar)
  adev=sqrt(avar);
  loglog(logspace(-2,2,1024),adev/fc)
  xlabel('tau (s)');ylabel('ADEV (no unit)')
  grid on
  hold on
  
  figure(98)
  subplot(211)
  % plot resulting mdev=sqrt(mvar)
  mdev=sqrt(mvar);
  loglog(logspace(-2,2,1024),mdev/fc)
  xlabel('tau (s)');ylabel('MDEV (no unit)')
  grid on
  hold on
end
legend('Class I','GM class II','BC class II')
figure(99)
legend('Class I','GM class II','BC class II')
