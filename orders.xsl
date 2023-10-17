<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<!--template correspond à la racine du XML-->
  <xsl:template match="/">
    <html>
      <head>
      <!--header contient le titre et le lien vers le fichier css-->
        <title>Orders Report</title>
        <link rel="stylesheet" type="text/css" href="styles.css"/>
      </head>
      <body>
        <h1>Orders Report</h1>
        <!--création d'un tableau pour afficher les informations-->
        <table border="1">
        <!--th pour table header-->
          <tr>
            <th>Order ID</th>
            <th>Description</th>
            <th>Price</th>
            <th>Invoice Date</th>
          </tr>
          <!--itération sur les éléments de Order-->
          <xsl:for-each select="Orders/Order">
            <!--Utilisation de xsl:variable pour stocker les valeurs afin de les réutiliser-->
            <xsl:variable name="orderID" select="OrderID"/>
            <xsl:variable name="invoiceDate" select="InvoiceDate"/>
            <!--Itération de tous les items-->
            <xsl:for-each select="Description">
              <!--vérification si premier item pour introduire orderID et invoiceDate-->
              <xsl:if test="position() = 1">
                <tr>
                  <!--orderId s'étend sur plusieurs lignes (en fonction du nbr d'items)-->
                  <td rowspan="{count(../Description)}">
                    <xsl:value-of select="$orderID"/>
                  </td>
                  <td>
                    <!--Texte de l'élément description-->
                    <xsl:value-of select="text()"/>
                  </td>
                  <td>
                    <!--Calcul du prix total en formatant pour avoir 2 décimales-->
                    <xsl:value-of select="format-number(Quantity * UnitPrice, '0.00')"/>
                  </td>
                  <td rowspan="{count(../Description)}">
                    <xsl:value-of select="$invoiceDate"/>
                  </td>
                </tr>
              </xsl:if>
              <xsl:if test="position() > 1">
                <tr>
                  <td>
                    <xsl:value-of select="text()"/>
                  </td>
                  <td>
                    <xsl:value-of select="format-number(Quantity * UnitPrice, '0.00')"/>
                  </td>
                </tr>
              </xsl:if>
            </xsl:for-each>
          </xsl:for-each>
        </table>
      </body>
    </html>
  </xsl:template>

</xsl:stylesheet>
