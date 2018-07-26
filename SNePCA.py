from __future__ import division

import SNIDsn
import SNIDdataset as snid

import numpy as np
import scipy

import matplotlib.pyplot as plt
import seaborn as sns
sns.set_color_codes('colorblind')
import matplotlib.patches as mpatches
import matplotlib.transforms as transforms
import matplotlib.gridspec as gridspec

import plotly.plotly as ply
import plotly.graph_objs as go
import plotly.tools as tls

import sklearn
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from scipy.spatial import distance

import pickle




class SNePCA:

    def __init__(self, snidset):
        self.snidset = snidset

        self.IIb_color = 'g'
        self.Ib_color = 'mediumorchid'
        self.Ic_color = 'r'
        self.IcBL_color = 'k'
        self.H_color = 'steelblue'
        self.He_color = 'indianred'

        
        nspec = snid.numSpec(self.snidset)
        snnames = self.snidset.keys()
        tmpobj = self.snidset[snnames[0]]
        nwvlbins = len(tmpobj.wavelengths)
        self.wavelengths = tmpobj.wavelengths

        specMatrix = np.ndarray((nspec, nwvlbins))
        count = 0
        for snname in snnames:
            snobj = self.snidset[snname]
            phasekeys = snobj.getSNCols()
            for phk in phasekeys:
                specMatrix[count,:] = snobj.data[phk]
                count = count + 1

        self.specMatrix = specMatrix

        return


    def getSNeTypeMasks(self):
        snnames = self.snidset.keys()
        typeinfo = snid.datasetTypeDict(self.snidset)
        IIblist = typeinfo['IIb']
        Iblist = typeinfo['Ib']
        Iclist = typeinfo['Ic']
        IcBLlist = typeinfo['IcBL']

        IIbmask = np.in1d(self.snidset.keys(), IIblist)
        Ibmask = np.in1d(self.snidset.keys(), Iblist)
        Icmask = np.in1d(self.snidset.keys(), Iclist)
        IcBLmask = np.in1d(self.snidset.keys(), IcBLlist)

        return IIbmask, Ibmask, Icmask, IcBLmask


    def snidPCA(self):
        pca = PCA()
        pca.fit(self.specMatrix)
        self.evecs = pca.components_
        self.evals = pca.explained_variance_ratio_
        self.evals_cs = self.evals.cumsum()
        self.pcaCoeffMatrix = np.dot(self.evecs, self.specMatrix.T).T

        for i, snname in enumerate(self.snidset.keys()):
            snobj = self.snidset[snname]
            snobj.pcaCoeffs = self.pcaCoeffMatrix[i,:]
        return

    def reconstructSpectrum(self, snname, phasekey, nPCAComponents, fontsize):
        snobj = self.snidset[snname]
        datasetMean = np.mean(self.specMatrix, axis=0)
        trueSpec = snobj.data[phasekey]
        pcaCoeff = np.dot(self.evecs, (trueSpec - datasetMean))
        f = plt.figure(figsize=(15,20))
        plt.tick_params(axis='both', which='both', bottom='off', top='off',\
                            labelbottom='off', labelsize=40, right='off', left='off', labelleft='off')
        f.subplots_adjust(hspace=0, top=0.95, bottom=0.1, left=0.12, right=0.93)
        
        for i, n in enumerate(nPCAComponents):
            ax = f.add_subplot(411 + i)
            ax.plot(snobj.wavelengths, trueSpec, '-', c='gray')
            ax.plot(snobj.wavelengths, datasetMean + (np.dot(pcaCoeff[:n], self.evecs[:n])), '-k')
            ax.tick_params(axis='both',which='both',labelsize=20)
            if i < len(nPCAComponents) - 1:
                plt.tick_params(
                axis='x',          # changes apply to the x-axis
                which='both',      # both major and minor ticks are affected
                bottom='off',      # ticks along the bottom edge are off
                top='off',         # ticks along the top edge are off
                labelbottom='off') # labels along the bottom edge are off
            ax.set_ylim(-2,2)

            if i == 0:
                # Balmer lines
                trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)
                trans2 = transforms.blended_transform_factory(ax.transAxes, ax.transAxes)

                ax.text(0.02,1.05, "(N PCA, % Var.)", fontsize=fontsize, horizontalalignment='left',\
                        verticalalignment='center', transform=trans2)

                ax.axvspan(6213, 6366, alpha=0.1, color=self.H_color) #H alpha -9000 km/s to -16000 km/s
                s = r'$\alpha$'
                xcord = (6213+6366)/2.0
                ax.text(xcord, 1.05, 'H'+s, fontsize=fontsize, horizontalalignment='center',\
                        verticalalignment='center',transform=trans)
                ax.axvspan(4602, 4715, alpha=0.1, color=self.H_color) #H Beta -9000 km/s to-16000 km/s
                s = r'$\beta$'
                xcord = (4602+4715)/2.0
                ax.text(xcord, 1.05, 'H'+s, fontsize=fontsize, horizontalalignment='center',\
                        verticalalignment='center',transform=trans)

                ax.axvspan(5621, 5758, alpha=0.1, color=self.He_color) #HeI5876 -6000 km/s to -13000 km/s
                ax.text((5621+5758)/2.0, 1.05, 'HeI5876', fontsize=fontsize, horizontalalignment='center',\
                        verticalalignment='center', transform=trans)
                ax.axvspan(6388, 6544, alpha=0.1, color=self.He_color)
                ax.text((6388+6544)/2.0, 1.05, 'HeI6678', fontsize=fontsize, horizontalalignment='center',\
                        verticalalignment='center', transform=trans)
                ax.axvspan(6729, 6924, alpha=0.1, color=self.He_color)
                ax.text((6729+6924)/2.0, 1.05, 'HeI7065', fontsize=fontsize, horizontalalignment='center',\
                        verticalalignment='center', transform=trans)
 



            if i > 0:
                # Balmer lines
                trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)
                ax.axvspan(6213, 6366, alpha=0.1, color=self.H_color) #H alpha -9000 km/s to -16000 km/s
                ax.axvspan(4602, 4715, alpha=0.1, color=self.H_color) #H Beta -9000 km/s to-16000 km/s
                ax.axvspan(5621, 5758, alpha=0.1, color=self.He_color) #HeI5876 -6000 km/s to -13000 km/s
                ax.axvspan(6388, 6544, alpha=0.1, color=self.He_color)
                ax.axvspan(6729, 6924, alpha=0.1, color=self.He_color)
            if n == 0:
                text = 'mean'
            elif n == 1:
                text = "1 component\n"
                text += r"$(\sigma^2_{tot} = %.2f)$" % self.evals_cs[n - 1]

            else:
                text = "%i components\n" % n
                text += r"$(\sigma^2_{tot} = %.2f)$" % self.evals_cs[n - 1]
                text = '(%i, %.0f'%(n, 100*self.evals_cs[n-1])+'%)'
            ax.text(0.02, 0.93, text, fontsize=20,ha='left', va='top', transform=ax.transAxes)
            f.axes[-1].set_xlabel(r'${\rm wavelength\ (\AA)}$',fontsize=30)
            f.text(0.07, 2.0/3.0, 'Relative Flux', verticalalignment='top', rotation='vertical', fontsize=16)
        return f


    def plotEigenspectra(self, figsize, nshow, ylim=None, fontsize=16):
        f = plt.figure(figsize=figsize)
        hostgrid = gridspec.GridSpec(3,1)
        hostgrid.update(hspace=0.2)

        eiggrid = gridspec.GridSpecFromSubplotSpec(nshow, 1, subplot_spec=hostgrid[:2,0], hspace=0)

        for i, ev in enumerate(self.evecs[:nshow]):
            ax = plt.subplot(eiggrid[i,0])
            ax.plot(self.wavelengths, ev, color=self.IcBL_color)

            trans2 = transforms.blended_transform_factory(ax.transAxes, ax.transAxes)
            ax.text(0.02,0.85, "(PCA%d, %.0f"%(i+1, 100*self.evals_cs[i])+'%)', horizontalalignment='left',\
                    verticalalignment='center', fontsize=fontsize, transform=trans2)
            ax.tick_params(axis='both',which='both',labelsize=fontsize)
            if not ylim is None:
                ax.set_ylim(ylim)
            if i > -1:
                yticks = ax.yaxis.get_major_ticks()
                yticks[-1].set_visible(False)

            if i == 0:
                # Balmer lines
                trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)
                trans2 = transforms.blended_transform_factory(ax.transAxes, ax.transAxes)

                ax.text(0.02,1.05, "(PCA#, Cum. Var.)", fontsize=fontsize, horizontalalignment='left',\
                        verticalalignment='center', transform=trans2)

                ax.axvspan(6213, 6366, alpha=0.1, color=self.H_color) #H alpha -9000 km/s to -16000 km/s
                s = r'$\alpha$'
                xcord = (6213+6366)/2.0
                ax.text(xcord, 1.05, 'H'+s, fontsize=fontsize, horizontalalignment='center',\
                        verticalalignment='center',transform=trans)
                ax.axvspan(4602, 4715, alpha=0.1, color=self.H_color) #H Beta -9000 km/s to-16000 km/s
                s = r'$\beta$'
                xcord = (4602+4715)/2.0
                ax.text(xcord, 1.05, 'H'+s, fontsize=fontsize, horizontalalignment='center',\
                        verticalalignment='center',transform=trans)


                ax.axvspan(5621, 5758, alpha=0.1, color=self.He_color) #HeI5876 -6000 km/s to -13000 km/s
                ax.text((5621+5758)/2.0, 1.05, 'HeI5876', fontsize=fontsize, horizontalalignment='center',\
                        verticalalignment='center', transform=trans)
                ax.axvspan(6388, 6544, alpha=0.1, color=self.He_color)
                ax.text((6388+6544)/2.0, 1.05, 'HeI6678', fontsize=fontsize, horizontalalignment='center',\
                        verticalalignment='center', transform=trans)
                ax.axvspan(6729, 6924, alpha=0.1, color=self.He_color)
                ax.text((6729+6924)/2.0, 1.05, 'HeI7065', fontsize=fontsize, horizontalalignment='center',\
                        verticalalignment='center', transform=trans)
            if i > 0:
                # Balmer lines
                trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)
                ax.axvspan(6213, 6366, alpha=0.1, color=self.H_color) #H alpha -9000 km/s to -16000 km/s
                ax.axvspan(4602, 4715, alpha=0.1, color=self.H_color) #H Beta -9000 km/s to-16000 km/s
                ax.axvspan(5621, 5758, alpha=0.1, color=self.He_color) #HeI5876 -6000 km/s to -13000 km/s
                ax.axvspan(6388, 6544, alpha=0.1, color=self.He_color)
                ax.axvspan(6729, 6924, alpha=0.1, color=self.He_color)


            if i == nshow - 1:
                ax.set_xlabel("Wavelength", fontsize=fontsize)

        ax = plt.subplot(hostgrid[-1])
        ax.boxplot(self.pcaCoeffMatrix)
        ax.set_xlabel('PCA Component #', fontsize=fontsize)
        ax.set_ylabel('PCA Coefficient Value', fontsize=fontsize)
        ax.tick_params(axis='both', which='both', labelsize=fontsize)
        ax.axhline(y=0, color=self.Ic_color)
        xticklabels = ax.xaxis.get_majorticklabels()
        xticklabels[0].set_visible
        for i, tick in enumerate(xticklabels):
            if i%4 != 0:
                tick.set_visible(False)

        #f.text(0.07, 2.0/3.0, 'Relative Flux', verticalalignment='center', rotation='vertical', fontsize=16)
        return f, hostgrid



    def pcaPlot(self, pcax, pcay, figsize, purity=False, std_rad=None):
        f = plt.figure(figsize=figsize)
        ax = plt.gca()
        red_patch = mpatches.Patch(color=self.Ic_color, label='Ic')
        cyan_patch = mpatches.Patch(color=self.Ib_color, label='Ib')
        black_patch = mpatches.Patch(color=self.IcBL_color, label='IcBL')
        green_patch = mpatches.Patch(color=self.IIb_color, label='IIb')

        IIbMask, IbMask, IcMask, IcBLMask = self.getSNeTypeMasks()

        x = self.pcaCoeffMatrix[:,pcax-1]
        y = self.pcaCoeffMatrix[:,pcay-1]

        #centroids
        IIbxmean = np.mean(x[IIbMask])
        IIbymean = np.mean(y[IIbMask])
        Ibxmean = np.mean(x[IbMask])
        Ibymean = np.mean(y[IbMask])
        Icxmean = np.mean(x[IcMask])
        Icymean = np.mean(y[IcMask])
        IcBLxmean = np.mean(x[IcBLMask])
        IcBLymean = np.mean(y[IcBLMask])
        plt.scatter(IIbxmean, IIbymean, color=self.IIb_color, alpha=0.5, s=100, marker='x')
        plt.scatter(Ibxmean, Ibymean, color=self.Ib_color, alpha=0.5, s=100, marker='x')
        plt.scatter(Icxmean, Icymean, color=self.Ic_color, alpha=0.5, s=100, marker='x')
        plt.scatter(IcBLxmean, IcBLymean, color=self.IcBL_color, alpha=0.5, s=100, marker='x')

        if purity:
            ncomp_arr = [pcax, pcay]
            keys, purity_rad_arr = self.purityEllipse(std_rad, ncomp_arr)
            IIbrad = purity_rad_arr[0]
            Ibrad = purity_rad_arr[1]
            IcBLrad = purity_rad_arr[2]
            Icrad = purity_rad_arr[3]

            ellipse_IIb = mpatches.Ellipse((IIbxmean, IIbymean),2*IIbrad[0],2*IIbrad[1], color=self.IIb_color, alpha=0.1)
            ellipse_Ib = mpatches.Ellipse((Ibxmean, Ibymean),2*Ibrad[0],2*Ibrad[1], color=self.Ib_color, alpha=0.1)
            ellipse_Ic = mpatches.Ellipse((Icxmean, Icymean),2*Icrad[0],2*Icrad[1], color=self.Ic_color, alpha=0.1)
            ellipse_IcBL = mpatches.Ellipse((IcBLxmean, IcBLymean),2*IcBLrad[0],2*IcBLrad[1], color=self.IcBL_color, alpha=0.1)

            ax.add_patch(ellipse_IIb)
            ax.add_patch(ellipse_Ib)
            ax.add_patch(ellipse_Ic)
            ax.add_patch(ellipse_IcBL)

        plt.scatter(x[IIbMask], y[IIbMask], color=self.IIb_color, alpha=1)
        plt.scatter(x[IbMask], y[IbMask], color=self.Ib_color, alpha=1)
        plt.scatter(x[IcMask], y[IcMask], color=self.Ic_color, alpha=1)
        plt.scatter(x[IcBLMask], y[IcBLMask], color=self.IcBL_color, alpha=1)
        #for i, name in enumerate(self.sneNames[IcBLMask]):
        #    plt.text(x[IcBLMask][i], y[IcBLMask][i], name)

        plt.xlim((np.min(x)-2,np.max(x)+2))
        plt.ylim((np.min(y)-2,np.max(y)+2))

        plt.ylabel('PCA Comp %d'%(pcay),fontsize=20)
        plt.xlabel('PCA Comp %d'%(pcax), fontsize=20)
#        plt.axis('off')
        plt.legend(handles=[red_patch, cyan_patch, black_patch, green_patch], fontsize=18)
        #plt.title('PCA Space Separability of IcBL and IIb SNe (Phase %d$\pm$%d Days)'%(self.loadPhase, self.phaseWidth),fontsize=22)
        plt.minorticks_on()
        plt.tick_params(
                    axis='both',          # changes apply to the x-axis
                    which='both',      # both major and minor ticks are affected
                    labelsize=20) # labels along the bottom edge are off

        return f



    def purityEllipse(self, std_rad, ncomp_array):
        ncomp_array = np.array(ncomp_array) - 1
        IIbMask, IbMask, IcMask, IcBLMask = self.getSNeTypeMasks()
        maskDict = {'IIb':IIbMask, 'Ib':IbMask, 'IcBL':IcBLMask, 'Ic':IcMask}
        keys = ['IIb', 'Ib', 'IcBL', 'Ic']
        masks = [IIbMask, IbMask, IcBLMask, IcMask]
        purity_rad_arr = []
        for key,msk in zip(keys,masks):
            centroid = np.mean(self.pcaCoeffMatrix[:,ncomp_array][msk], axis=0)
            print 'centroid', centroid
            dist_from_centroid = np.abs(self.pcaCoeffMatrix[:,ncomp_array][msk] - centroid)
            mean_dist_from_centroid = np.mean(dist_from_centroid, axis=0)
            print 'mean dist from centroid: ', mean_dist_from_centroid
            std_dist_all_components = np.std(dist_from_centroid, axis=0)
            print 'std dist from centroid: ', std_dist_all_components
            purity_rad_all = mean_dist_from_centroid + std_rad * std_dist_all_components
            print 'purity rad all components: ', purity_rad_all
            purity_rad_arr.append(purity_rad_all)


            ellipse_cond = np.sum(np.power((self.pcaCoeffMatrix[:,ncomp_array] - centroid), 2)/\
                                  np.power(purity_rad_all, 2), axis=1)
            print 'ellipse condition: ', ellipse_cond
            purity_msk = ellipse_cond < 1

            print key
            print 'purity radius: ', purity_rad_all
            print '# of SNe within purity ellipse for type '+key+': ',np.sum(purity_msk)
            names_within_purity_rad = np.array(self.snidset.keys())[purity_msk]
            correct_names = np.array(self.snidset.keys())[msk]
            correct_msk = np.isin(names_within_purity_rad, correct_names)
            print '# of correct SNe '+key+': ', np.sum(correct_msk)
        return keys, purity_rad_arr


    def pcaPlotly(self, pcaxind, pcayind, std_rad):
        IIbmask, Ibmask, Icmask, IcBLmask = self.getSNeTypeMasks()
        pcax = self.pcaCoeffMatrix[:,pcaxind - 1]
        pcay = self.pcaCoeffMatrix[:,pcayind - 1]
        col_red = 'rgba(152,0,0,1)'
        col_blue = 'rgba(0,152,152,1)'
        col_green = 'rgba(0,152,0,1)'
        col_black = 'rgba(0,0,0,152)'
        col_purp = 'rgba(186,85,211, 0.8)'

        traceIIb=go.Scatter(x=pcax[IIbmask], y=pcay[IIbmask], mode='markers',\
                            marker=dict(size=10, line=dict(width=1), color=col_green, opacity=1), \
                            text=np.array(self.snidset.keys())[IIbmask], name='IIb')
        
        traceIb=go.Scatter(x=pcax[Ibmask], y=pcay[Ibmask], mode='markers',\
                            marker=dict(size=10, line=dict(width=1), color=col_purp, opacity=1), \
                            text=np.array(self.snidset.keys())[Ibmask], name='Ib')
        
        traceIc=go.Scatter(x=pcax[Icmask], y=pcay[Icmask], mode='markers',\
                            marker=dict(size=10, line=dict(width=1), color=col_red, opacity=1), \
                            text=np.array(self.snidset.keys())[Icmask], name='Ic')
        
        traceIcBL=go.Scatter(x=pcax[IcBLmask], y=pcay[IcBLmask], mode='markers',\
                            marker=dict(size=10, line=dict(width=1), color=col_black, opacity=1), \
                            text=np.array(self.snidset.keys())[IcBLmask], name='IcBL')
        data = [traceIIb, traceIb, traceIc, traceIcBL]


        #centroids
        IIbxmean = np.mean(pcax[IIbmask])
        IIbymean = np.mean(pcay[IIbmask])
        Ibxmean = np.mean(pcax[Ibmask])
        Ibymean = np.mean(pcay[Ibmask])
        Icxmean = np.mean(pcax[Icmask])
        Icymean = np.mean(pcay[Icmask])
        IcBLxmean = np.mean(pcax[IcBLmask])
        IcBLymean = np.mean(pcay[IcBLmask])
        
        keys, purityrad = self.purityEllipse(std_rad, [pcaxind, pcayind])
        IIbradx = purityrad[0][0]
        IIbrady = purityrad[0][1]
        Ibradx = purityrad[1][0]
        Ibrady = purityrad[1][1]
        IcBLradx = purityrad[2][0]
        IcBLrady = purityrad[2][1]
        Icradx = purityrad[3][0]
        Icrady = purityrad[3][1]

        layout = go.Layout(autosize=False,
               width=1000,
               height=700,
               xaxis=dict(
                   title='PCA%i'%(pcaxind),
                   titlefont=dict(
                       family='Courier New, monospace',
                       size=30,
                       color='black'
                   ),
               ),
               yaxis=dict(
                   title='PCA%i'%(pcayind),
                   titlefont=dict(
                       family='Courier New, monospace',
                       size=30,
                       color='black'
                   ),
               ), shapes=[
                   {
                       'type': 'circle',
                       'xref': 'x',
                       'yref': 'y',
                       'x0': IIbxmean-IIbradx,
                       'y0': IIbymean - IIbrady,
                       'x1': IIbxmean+IIbradx,
                       'y1': IIbymean + IIbrady,
                       'opacity': 0.2,
                       'fillcolor': col_green,
                       'line': {
                           'color': col_green,
                       },
                   },
               {
                       'type': 'circle',
                       'xref': 'x',
                       'yref': 'y',
                       'x0': Ibxmean - Ibradx,
                       'y0': Ibymean - Ibrady,
                       'x1': Ibxmean + Ibradx,
                       'y1': Ibymean + Ibrady,
                       'opacity': 0.2,
                       'fillcolor': col_purp,
                       'line': {
                           'color': col_purp,
                       },
                   },{
                       'type': 'circle',
                       'xref': 'x',
                       'yref': 'y',
                       'x0': Icxmean - Icradx,
                       'y0': Icymean - Icrady,
                       'x1': Icxmean + Icradx,
                       'y1': Icymean + Icrady,
                       'opacity': 0.2,
                       'fillcolor': col_red,
                       'line': {
                           'color': col_red
                       }
                   },{
                       'type': 'circle',
                       'xref': 'x',
                       'yref': 'y',
                       'x0': IcBLxmean - IcBLradx,
                       'y0': IcBLymean - IcBLrady,
                       'x1': IcBLxmean + IcBLradx,
                       'y1': IcBLymean + IcBLrady,
                       'opacity': 0.2,
                       'fillcolor': col_black,
                       'line': {
                           'color': col_black
                       }
                   }]
           )
        fig = go.Figure(data=data, layout=layout)
        return fig



